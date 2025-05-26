import json
import csv
import pandas as pd
import numpy as np

# 计算 RSI
def calculate_rsi(data, period=14):
    delta = data['收盘价'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    
    roll_up1 = up.rolling(period).mean()
    roll_down1 = down.abs().rolling(period).mean()
    
    RS = roll_up1 / roll_down1
    RSI = 100.0 - (100.0 / (1.0 + RS))
    return RSI

with open('data/all_stocks.json', 'r', encoding='utf-8') as f:
    stock_list = json.load(f)

# 限制股票数量
stock_list = stock_list[:5]
for stock in stock_list:
    stock_code = stock['stock_code']
    try:
        # CSV 文件路径
        csv_file_path = f'data/stock_data/{stock_code}.csv'
        
        # 读取 CSV 文件
        df = pd.read_csv(csv_file_path, encoding='utf-8')

        # 确保 '收盘价' 列存在且不为空
        if '收盘价' not in df.columns or df['收盘价'].isnull().all():
            print(f'{stock_code}：收盘价数据缺失，无法计算 RSI')
            #  如果文件不存在或者 '收盘价' 列缺失，则直接结束
            exit()

        # 计算 RSI
        rsi = calculate_rsi(df)

        # 获取最新的 RSI 值
        if pd.isna(rsi.iloc[-1]):
            print(f'{stock_code}：RSI计算结果为NaN')
            exit()
        last_rsi = rsi.iloc[-1]

        # 筛选 RSI 值大于 70 的股票
        if last_rsi > 70:
            print(f'{stock_code}：RSI = {last_rsi:.2f} > 70，符合筛选条件')
        else:
            print(f'{stock_code}：RSI = {last_rsi:.2f} <= 70')

    except FileNotFoundError:
        print(f'文件 {csv_file_path} 不存在')
    except Exception as e:
        print(f'{stock_code} 历史数据获取失败: {e}')
