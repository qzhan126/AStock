"""
示例脚本：获取一系列股票的历史K线数据并将其保存到单独的CSV文件中。

该脚本演示了如何：
- 从JSON文件（'data/all_stocks.json'）加载股票代码列表。
  如果文件不存在，则尝试自动从API获取并保存。
- 遍历每个股票代码。
- 调用 `src.api_client` 中的 `fetch_stock_history` 函数获取K线数据。
- 处理返回的数据。
- 使用 `src.utils` 中的 `save_to_csv` 函数和 `KLINE_CSV_HEADER`
  将K线数据保存到 'data/stock_data/' 目录下的CSV文件中。
- 处理在获取或文件操作过程中可能发生的错误。
- 包含一个可选的API调用之间的延迟，以避免对服务器造成过大压力。
"""
import json
import os
import time # 用于在API调用之间添加延迟
# import pandas as pd # 重构后此脚本不再直接使用
# import numpy as np # 未使用
# import requests # 现在由 api_client 处理
# import re # 现在由 api_client 处理
# import csv # 现在由 utils.save_to_csv 处理

from src.api_client import fetch_stock_history, fetch_stock_list # 添加了 fetch_stock_list
from src.utils import save_to_csv, KLINE_CSV_HEADER, save_to_json # 添加了 save_to_json


# --- 配置 ---
DATA_ALL_STOCKS_FILE_PATH = 'data/all_stocks.json' # 包含股票列表的JSON文件路径
OUTPUT_DIR = 'data/stock_data'          # 保存获取的CSV数据的目录
KLINE_TYPE = 101                        # K线类型 (101 表示日线)
API_DELAY_SECONDS = 1                   # API调用之间的延迟秒数

# --- 主脚本执行 ---

# 加载待处理的股票列表
stock_list_to_process = [] # 初始化

if not os.path.exists(DATA_ALL_STOCKS_FILE_PATH):
    print(f"提示：`{DATA_ALL_STOCKS_FILE_PATH}` 未找到，将尝试自动获取并保存。")
    fetched_stocks = fetch_stock_list() # 调用API获取股票列表
    if fetched_stocks:
        # 保存前确保 'data' 目录存在
        os.makedirs(os.path.dirname(DATA_ALL_STOCKS_FILE_PATH), exist_ok=True)
        save_to_json(fetched_stocks, DATA_ALL_STOCKS_FILE_PATH) # 保存到JSON文件
        print(f"提示：已成功获取并保存股票列表到 `{DATA_ALL_STOCKS_FILE_PATH}`。")
        stock_list_to_process = fetched_stocks
    else:
        print(f"错误：自动获取股票列表失败。请确保网络连接正常或手动创建 `{DATA_ALL_STOCKS_FILE_PATH}`。")
        exit(1) # 如果无法获取股票列表，则退出脚本
else:
    try:
        with open(DATA_ALL_STOCKS_FILE_PATH, 'r', encoding='utf-8') as f:
            stock_list_to_process = json.load(f)
    except FileNotFoundError: # 理论上应由外部if捕获，此处作为安全措施
        print(f"错误：`{DATA_ALL_STOCKS_FILE_PATH}` 未找到。")
        exit(1)
    except json.JSONDecodeError:
        print(f"错误：`{DATA_ALL_STOCKS_FILE_PATH}` 文件格式错误，无法解析JSON。")
        exit(1)


# 可选：限制处理的股票数量（例如，用于测试）
# stock_list_to_process = stock_list_to_process[:5] # 示例：仅处理前5只股票


# 确保股票数据的输出目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"已创建输出目录: {OUTPUT_DIR}")

# 遍历列表中的每只股票
# 现在 stock_info 预期为一个字典，例如 {'code': '000001', 'name': '平安银行'}
for stock_info in stock_list_to_process:
    stock_code = stock_info['code'] # 使用 'code' 键获取股票代码
    stock_name = stock_info.get('name', stock_code) # 使用 'name' 键获取股票名称，如果缺失则回退到代码
    print(f"正在处理股票: {stock_name} ({stock_code})...")
    
    # 定义输出CSV文件的路径（使用股票代码命名）
    csv_file_path = os.path.join(OUTPUT_DIR, f'{stock_code}.csv')

    # 可选：如果CSV文件已存在，则跳过下载
    if os.path.exists(csv_file_path):
        print(f"{stock_name} ({stock_code}) 的数据已存在于 {csv_file_path}。跳过下载。")
        continue

    try:
        # 使用api_client中的函数获取股票历史数据（使用股票代码）
        # klt=KLINE_TYPE 指定K线周期（例如，日线、周线）
        history_data_response = fetch_stock_history(stock_code=stock_code, klt=KLINE_TYPE)

        # 处理响应
        if history_data_response and history_data_response.get('data') and history_data_response['data'].get('klines'):
            klines_raw_list = history_data_response['data']['klines'] # 字符串列表，每个字符串是一条K线记录
            
            if not klines_raw_list:
                print(f"在API响应中未找到 {stock_name} ({stock_code}) 的K线数据 (klines列表为空)。")
                continue

            # 将K线字符串列表转换为列表的列表（用于CSV的行）
            # klines_raw_list 中的每个字符串都是逗号分隔的。
            processed_kline_data_for_csv = [kline_record.split(',') for kline_record in klines_raw_list]
            
            # 使用工具函数将处理后的数据保存到CSV文件
            # KLINE_CSV_HEADER 提供CSV文件的标题行。
            save_to_csv(csv_file_path, processed_kline_data_for_csv, KLINE_CSV_HEADER)
            print(f"已成功获取并保存 {stock_name} ({stock_code}) 的数据到 {csv_file_path}")

        # 处理API可能返回成功状态但没有实际 'data' 或 'klines' 字段的情况
        elif history_data_response and history_data_response.get('data') is None:
             print(f"警告：{stock_name} ({stock_code}) 的API响应缺少 'data' 字段，尽管请求可能已成功。响应：{history_data_response}")
        else:
            # 处理其他获取失败或数据为空的情况
            print(f"警告：未能获取 {stock_name} ({stock_code}) 的数据，或响应中不包含K线数据。响应：{history_data_response}")

        # 实现延迟以避免对API服务器造成过大压力并防止速率限制
        print(f"等待 {API_DELAY_SECONDS} 秒后进行下一次请求...")
        time.sleep(API_DELAY_SECONDS)

    except Exception as e:
        # 捕获处理特定股票时可能发生的任何其他异常
        print(f"处理 {stock_name} ({stock_code}) 时发生意外错误: {e}")
        # 可选：此处可以将 stock_code 添加到失败尝试列表中

print("\n股票数据获取过程已完成。")
