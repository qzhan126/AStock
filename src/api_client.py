# src/api_client.py
import requests
from urllib.parse import urlencode
import config
import re
import akshare as ak

def fetch_stock_list():
    """
    获取股票列表
    """
    try:
        stock_list = ak.stock_zh_stock_name_all()
        stock_list = stock_list["name"].tolist()
        return stock_list
    except Exception as e:
        print(f"Error fetching stock list: {e}")
        return None

def fetch_stock_history(secid, klt):
    """
    获取股票历史数据
    """
    api_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&beg=0&end=20500101&ut=fa5fd1943c7b386f172d6893dbfba10b&rtntype=6&klt=60&fqt=1&cb=callback&lmt=1000&secid={secid}"
    url = api_url.format(secid=secid)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        jsonp_str = response.text
        json_str = re.search(r'callback\((.*)\)', jsonp_str).group(1)
        data = json.loads(json_str)
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stock history: {e}")
        return None