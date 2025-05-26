# src/utils.py
import json
import csv

# KLINE_CSV_HEADER 定义了K线数据CSV文件的列标题。
# 这些标题对应东方财富API返回的历史股票数据字段。
KLINE_CSV_HEADER = ['日期', '开盘价', '收盘价', '最高价', '最低价', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']

def save_to_json(data: dict, filename: str):
    """
    将给定的字典数据以UTF-8编码和缩进格式保存到JSON文件。

    :param data: 包含待保存数据的字典。
    :param filename: 要保存JSON数据的文件名。
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_to_csv(filepath: str, data: list[list[str]], header: list[str]):
    """
    将给定的表格数据以UTF-8编码保存到CSV文件。

    :param filepath: 要创建/覆盖的CSV文件的路径。
    :param data: 行数据列表，其中每行是一个字符串列表（单元格值）。
    :param header: 代表CSV文件标题行的字符串列表。
    """
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)