# src/utils.py
import json
import csv

# KLINE_CSV_HEADER defines the column headers for the K-line data CSV files.
# These correspond to the fields returned by the Eastmoney API for historical stock data.
KLINE_CSV_HEADER = ['日期', '开盘价', '收盘价', '最高价', '最低价', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']

def save_to_json(data: dict, filename: str):
    """
    Saves the given data dictionary to a JSON file with UTF-8 encoding and indentation.

    :param data: The dictionary containing data to be saved.
    :param filename: The name of the file to save the JSON data to.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_to_csv(filepath: str, data: list[list[str]], header: list[str]):
    """
    Saves the given tabular data to a CSV file with UTF-8 encoding.

    :param filepath: The path to the CSV file to be created/overwritten.
    :param data: A list of rows, where each row is a list of strings (cell values).
    :param header: A list of strings representing the header row of the CSV file.
    """
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)