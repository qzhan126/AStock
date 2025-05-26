import json
import requests
import re
import os
import time
import csv
import pandas as pd
import numpy as np

# 东方财富 API 链接
api_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&beg=0&end=20500101&ut=fa5fd1943c7b386f172d6893dbfba10b&rtntype=6&klt=60&fqt=1&cb=callback&lmt=1000&secid={secid}"

# 读取股票列表
with open('data/all_stocks.json', 'r', encoding='utf-8') as f:
    stock_list = json.load(f)

# 限制股票数量

# 创建 data/stock_data 目录，如果不存在
if not os.path.exists('data/stock_data'):
    os.makedirs('data/stock_data')

for stock in stock_list:
    stock_code = stock['stock_code']
    try:
        # CSV 文件路径
        csv_file_path = f'data/stock_data/{stock_code}.csv'

        # 检查 CSV 文件是否存在
        if os.path.exists(csv_file_path):
            # 从 CSV 文件读取数据
            df = pd.read_csv(csv_file_path, encoding='utf-8')
            print(f'{stock_code}：从 CSV 文件读取数据')
        else:
            # 判断股票代码属于哪个交易所
            if stock_code.startswith('6'):
                secid = f'1.{stock_code}'  # 上海交易所
            else:
                secid = f'0.{stock_code}'  # 深圳交易所

            # 构造完整的 API URL
            full_api_url = api_url.format(secid=secid)

            # 发送 HTTP 请求，添加重试机制
            max_retries = 1
            for retry in range(max_retries):
                try:
                    response = requests.get(full_api_url)
                    response.raise_for_status()  # 检查请求是否成功
                    break  # 请求成功，跳出循环
                except requests.exceptions.RequestException as e:
                    print(f'{stock_code}：连接失败，正在重试 ({retry + 1}/{max_retries}) - {e}')
                    if retry == max_retries - 1:
                        print(f'{stock_code}：达到最大重试次数，放弃获取')
                        raise  # 达到最大重试次数，抛出异常
                    time.sleep(5)  # 等待 5 秒后重试

            # 解析 JSONP 响应
            jsonp_str = response.text
            json_str = re.search(r'callback\((.*)\)', jsonp_str).group(1)
            data = json.loads(json_str)

            # 提取 k 线数据
            kline_data = data['data']['klines']

            # 将历史数据保存到 CSV 文件，例如 data/stock_data/{stock_code}.csv'
            with open(csv_file_path, 'w', encoding='utf-8', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)

                # 写入 CSV 文件的头部
                header = ['日期', '开盘价', '最高价', '最低价', '收盘价', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
                csv_writer.writerow(header)

                # 写入 CSV 文件的内容
                for kline in kline_data:
                    kline_values = kline.split(',')
                    csv_writer.writerow(kline_values)

            print(f'{stock_code}：从 API 获取数据并保存到 CSV 文件')
            
            # 读取 CSV 文件
            df = pd.read_csv(csv_file_path, encoding='utf-8')
    except Exception as e:
        print(f'{stock_code} 历史数据获取失败: {e}')
