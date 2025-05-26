# src/utils.py
import json
import csv

def save_to_json(data, filename):
    """
    将数据保存到 JSON 文件
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_to_csv(data, filename):
    """
    将数据保存到 CSV 文件
    """
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # 写入表头
        if data and data[list(data.keys())[0]] and data[list(data.keys())[0]]['data'] and data[list(data.keys())[0]]['data']['klines']:
            header = data[list(data.keys())[0]]['data']['klines'][0].split(',')
            writer.writerow(['股票代码'] + header)
        # 写入数据
        for code, history in data.items():
            if history and history['data'] and history['data']['klines']:
                for kline in history['data']['klines']:
                    row = kline.split(',')
                    writer.writerow([code] + row)