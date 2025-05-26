# src/api_client.py
import requests
import re
import akshare as ak
import json # Added import
import time # Added import
from src.config import EASTMONEY_HISTORY_API_URL # Import from config

def _generate_secid(stock_code: str) -> str:
    """
    Generates the 'secid' parameter required by the Eastmoney API.
    The 'secid' is a combination of a prefix (1 for Shanghai, 0 for Shenzhen)
    and the stock code.

    :param stock_code: Stock code (e.g., "600000" for Shanghai, "000001" for Shenzhen).
    :return: The formatted 'secid' string (e.g., "1.600000", "0.000001").
    """
    # Shanghai Stock Exchange (SSE) stock codes typically start with '6'.
    # Shenzhen Stock Exchange (SZSE) stock codes typically start with '0' or '3'.
    if stock_code.startswith('6'):
        return f"1.{stock_code}"
    else:
        return f"0.{stock_code}"

def fetch_stock_list():
    """
    Fetches a list of all A-share stock names using the akshare library.

    :return: A list of stock names, or None if an error occurs.
    """
    try:
        # ak.stock_zh_stock_name_all() returns a DataFrame with columns like 'code', 'name'
        stock_df = ak.stock_zh_stock_name_all()
        stock_list = stock_list["name"].tolist()
        return stock_list
    except Exception as e:
        print(f"Error fetching stock list: {e}")
        return None

def fetch_stock_history(stock_code: str, klt: int = 101, beg_date: str = '0', end_date: str = '20500101', limit: int = 1000):
    """
    Fetches historical K-line data for a given stock code from the Eastmoney API.

    The function attempts to fetch data up to 3 times in case of request failures,
    with a 3-second delay between retries.

    :param stock_code: The stock code (e.g., "600000", "000001").
    :param klt: K-line type. Defaults to 101 (daily).
                Other common values: 102 (weekly), 103 (monthly), 60 (60-minute).
    :param beg_date: Start date for the data, in 'YYYYMMDD' format. Defaults to '0' (earliest available).
    :param end_date: End date for the data, in 'YYYYMMDD' format. Defaults to '20500101' (a far future date).
    :param limit: The maximum number of K-line data points to retrieve. Defaults to 1000.
    :return: A dictionary containing the parsed JSON response from the API,
             or None if the request fails after all retries or if JSON parsing fails.
             The structure of the returned dictionary typically includes:
             {
                 "rc": 0, # Return code, 0 for success
                 "rt": 1,
                 "svr": 183630093,
                 "lt": 1,
                 "full": 0,
                 "data": {
                     "code": "000001",
                     "market": 0, # 0 for SZSE, 1 for SSE
                     "name": "平安银行",
                     "qtlist": null,
                     "klines": [
                         "YYYY-MM-DD,open,close,high,low,volume,amount,amplitude,pct_change_rate,pct_change_amount,turnover_rate",
                         ...
                     ],
                     "prec": 2, # Price precision
                     "total": 4848, # Total k-lines available
                     "decimal": 2
                 }
             }
             Returns None if data cannot be fetched or parsed.
    """
    secid = _generate_secid(stock_code)
    
    # Parameters for the Eastmoney API request
    # fields1 and fields2 specify the data fields to be returned.
    # ut is a user token, seems fixed.
    # rtntype=6 indicates JSONP response.
    # fqt=1 for forward-adjusted prices.
    # cb=callback is the JSONP callback function name.
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13", # Standard K-line fields
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61", # Additional data like turnover rate
        "beg": beg_date,
        "end": end_date,
        "ut": "fa5fd1943c7b386f172d6893dbfba10b", # Unique token, seems to be static
        "rtntype": "6", # Response type: 5 for JSON, 6 for JSONP
        "klt": str(klt),
        "fqt": "1", # Adjust prices: 0 (none), 1 (forward), 2 (backward)
        "cb": "callback", # JSONP callback function name (fixed for this API)
        "lmt": str(limit),
        "secid": secid,
    }
    
    retries = 3 # Number of retry attempts
    for attempt in range(retries):
        try:
            response = requests.get(EASTMONEY_HISTORY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            jsonp_str = response.text
            if jsonp_str.startswith('callback(') and jsonp_str.endswith(')'):
                # Strip "callback(" from the beginning and ")" from the end to get the JSON string
                json_str = jsonp_str[len('callback('):-1]
            else:
                # If not in the expected JSONP format, log a warning and try to parse as plain JSON.
                # This might happen if the API changes or returns an error message in plain JSON.
                print(f"Warning: Response for {stock_code} not in expected JSONP format. Attempting to parse as plain JSON.")
                json_str = jsonp_str
            
            try:
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as json_e:
                print(f"Error decoding JSON: {json_e}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching stock history (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(3)  # Wait for 3 seconds before retrying
            else:
                # If this is the last attempt, return None (or could raise the exception e)
                print(f"Failed to fetch data for {stock_code} after {retries} attempts.")
                return None 
    return None # Should only be reached if all retries fail