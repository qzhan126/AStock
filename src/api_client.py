# src/api_client.py
import requests
import re
import akshare as ak
import json # 导入json模块
import time # 导入time模块
from src.config import EASTMONEY_HISTORY_API_URL # 从config导入东方财富历史数据API URL

def _generate_secid(stock_code: str) -> str:
    """
    生成东方财富API所需的'secid'参数。
    'secid'是前缀（上海为1，深圳为0）和股票代码的组合。

    :param stock_code: 股票代码 (例如, 上海的 "600000", 深圳的 "000001")。
    :return: 格式化的'secid'字符串 (例如, "1.600000", "0.000001")。
    """
    # 上海证券交易所 (SSE) 的股票代码通常以 '6' 开头。
    # 深圳证券交易所 (SZSE) 的股票代码通常以 '0' 或 '3' 开头。
    if stock_code.startswith('6'):
        return f"1.{stock_code}"
    else:
        return f"0.{stock_code}"

def fetch_stock_list():
    """
    使用akshare库获取所有A股股票的代码和名称列表。

    :return: 包含股票代码和名称的字典列表 (例如, [{'code': '000001', 'name': '平安银行'}, ...]),
             如果发生错误则返回None。
    """
    try:
        # ak.stock_zh_stock_name_all() 返回一个包含 'code', 'name' 等列的DataFrame
        stock_df = ak.stock_zh_stock_name_all()
        # 将DataFrame转换为字典列表
        # 根据典型的akshare输出，使用 'code' 作为 stock_code，'name' 作为 stock_name
        stock_list = stock_df[['code', 'name']].to_dict(orient='records')
        return stock_list
    except Exception as e:
        print(f"获取股票列表时发生错误: {e}")
        return None

def fetch_stock_history(stock_code: str, klt: int = 101, beg_date: str = '0', end_date: str = '20500101', limit: int = 1000):
    """
    从东方财富API获取给定股票代码的历史K线数据。

    如果请求失败，函数会尝试最多获取3次数据，每次重试之间有3秒的延迟。

    :param stock_code: 股票代码 (例如, "600000", "000001")。
    :param klt: K线类型。默认为101 (日线)。
                其他常用值: 102 (周线), 103 (月线), 60 (60分钟线)。
    :param beg_date: 数据开始日期，格式为 'YYYYMMDD'。默认为 '0' (最早可用数据)。
    :param end_date: 数据结束日期，格式为 'YYYYMMDD'。默认为 '20500101' (一个遥远的未来日期)。
    :param limit: 要检索的最大K线数据点数。默认为1000。
    :return: 包含从API解析的JSON响应的字典，
             如果在所有重试后请求失败或JSON解析失败，则返回None。
             返回字典的结构通常包括:
             {
                 "rc": 0, # 返回码, 0表示成功
                 "rt": 1,
                 "svr": 183630093,
                 "lt": 1,
                 "full": 0,
                 "data": {
                     "code": "000001",
                     "market": 0, # 0表示深交所, 1表示上交所
                     "name": "平安银行",
                     "qtlist": null,
                     "klines": [
                         "YYYY-MM-DD,开盘价,收盘价,最高价,最低价,成交量,成交额,振幅,涨跌幅,涨跌额,换手率",
                         ...
                     ],
                     "prec": 2, # 价格精度
                     "total": 4848, # 可用的总K线条数
                     "decimal": 2
                 }
             }
             如果无法获取或解析数据，则返回None。
    """
    secid = _generate_secid(stock_code)
    
    # 东方财富API请求参数
    # fields1 和 fields2 指定要返回的数据字段。
    # ut 是用户令牌，似乎是固定的。
    # rtntype=6 表示JSONP响应。
    # fqt=1 表示前复权价格。
    # cb=callback 是JSONP回调函数名。
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13", # 标准K线字段
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61", # 附加数据，如换手率
        "beg": beg_date,
        "end": end_date,
        "ut": "fa5fd1943c7b386f172d6893dbfba10b", # 唯一令牌，似乎是静态的
        "rtntype": "6", # 响应类型: 5为JSON, 6为JSONP
        "klt": str(klt),
        "fqt": "1", # 复权类型: 0 (不复权), 1 (前复权), 2 (后复权)
        "cb": "callback", # JSONP回调函数名 (此API固定)
        "lmt": str(limit),
        "secid": secid,
    }
    
    retries = 3 # 重试次数
    for attempt in range(retries):
        try:
            response = requests.get(EASTMONEY_HISTORY_API_URL, params=params, timeout=10)
            response.raise_for_status() # 如果请求失败则引发HTTPError
            jsonp_str = response.text
            if jsonp_str.startswith('callback(') and jsonp_str.endswith(')'):
                # 从开头剥离 "callback("，从末尾剥离 ")" 以获取JSON字符串
                json_str = jsonp_str[len('callback('):-1]
            else:
                # 如果不是预期的JSONP格式，记录警告并尝试解析为普通JSON。
                # 如果API更改或以普通JSON格式返回错误消息，则可能发生这种情况。
                print(f"警告: {stock_code} 的响应未使用预期的JSONP格式。正在尝试解析为普通JSON。")
                json_str = jsonp_str
            
            try:
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as json_e:
                print(f"解码JSON时发生错误: {json_e}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"获取股票历史数据时发生错误 (尝试 {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(3)  # 重试前等待3秒
            else:
                # 如果这是最后一次尝试，则返回None (或者可以引发异常 e)
                print(f"在 {retries} 次尝试后未能获取 {stock_code} 的数据。")
                return None 
    return None # 只有在所有重试都失败时才应到达此处