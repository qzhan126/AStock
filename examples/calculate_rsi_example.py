"""
Example script to calculate the Relative Strength Index (RSI) for stocks
from their historical data stored in CSV files.

This script demonstrates how to:
- Load a list of stock codes from a JSON file ('data/all_stocks.json').
- For each stock:
    - Read its historical data from a CSV file located in 'data/stock_data/'.
    - Calculate the RSI using a specified period (default 14 days).
    - Print the latest RSI value.
    - Identify and print stocks with an RSI value greater than 70 (a common overbought signal).
- Handle potential errors like missing files or data issues.
"""
import json
# import csv # Not directly used, pandas handles CSV reading
import pandas as pd
import numpy as np # Used in calculate_rsi for NaN handling if extended

# --- Configuration ---
STOCK_LIST_FILE = 'data/all_stocks.json'  # Path to the JSON file containing the list of stocks
DATA_DIR = 'data/stock_data'             # Directory where individual stock CSV files are stored
RSI_PERIOD = 14                          # Period for RSI calculation
RSI_OVERBOUGHT_THRESHOLD = 70            # Threshold for identifying overbought stocks

# --- RSI Calculation Function ---
def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI) for a given dataset.

    :param data: Pandas DataFrame with a '收盘价' (Closing Price) column.
    :param period: The period (number of days) to use for RSI calculation. Default is 14.
    :return: Pandas Series containing the RSI values. The index will match the input DataFrame's index.
             Returns an empty Series if '收盘价' is not found or if calculations fail.
    """
    if '收盘价' not in data.columns:
        print("Error: '收盘价' (Closing Price) column not found in DataFrame.")
        return pd.Series(dtype=float) # Return empty series if required column is missing

    delta = data['收盘价'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0 # Gains
    down[down > 0] = 0 # Losses (as positive values)

    # Calculate the Exponential Moving Average (EMA) or Simple Moving Average (SMA)
    # Using SMA here as per the original simple implementation:
    avg_gain = up.rolling(window=period, min_periods=1).mean()
    avg_loss = down.abs().rolling(window=period, min_periods=1).mean()
    
    # Calculate Relative Strength (RS)
    # Avoid division by zero if avg_loss is 0; RSI would be 100 in such cases.
    rs = avg_gain / avg_loss
    rs = rs.replace([np.inf, -np.inf], np.nan) # Handle cases where avg_loss might be zero initially
    rs = rs.fillna(method='bfill') # Backfill NaNs which can occur if avg_loss was 0 for some initial periods

    # Calculate RSI
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # For periods where avg_loss is 0 and avg_gain is positive, RSI should be 100.
    # For periods where avg_gain is 0 and avg_loss is 0, RSI is often considered neutral (e.g. 50 or undefined).
    # The formula 100 - (100 / (1 + RS)) handles RS -> infinity (avg_loss=0) correctly as RSI -> 100.
    # If RS is 0 (avg_gain=0, avg_loss > 0), RSI is 0.
    # If both are 0, RS is NaN, which we've tried to handle. If RS is 0/0 -> NaN, RSI will be NaN.
    
    return rsi

# --- Main script execution ---

# Load the list of stocks to process
try:
    with open(STOCK_LIST_FILE, 'r', encoding='utf-8') as f:
        stock_list_full = json.load(f)
except FileNotFoundError:
    print(f"Error: '{STOCK_LIST_FILE}' not found. Ensure the file exists or you are running from the project root.")
    stock_list_full = []

# Optional: Limit the number of stocks for processing (e.g., for testing)
# stock_list_to_process = stock_list_full[:5] # Example: process only the first 5 stocks
stock_list_to_process = stock_list_full

print(f"Starting RSI calculation for {len(stock_list_to_process)} stocks...\n")

# Iterate through each stock
for stock_info in stock_list_to_process:
    stock_code = stock_info['stock_code']
    print(f"--- Processing: {stock_code} ---")
    
    # Construct the path to the stock's CSV data file
    csv_file_path = f'{DATA_DIR}/{stock_code}.csv'
    
    try:
        # Read the historical stock data from the CSV file
        df = pd.read_csv(csv_file_path, encoding='utf-8')

        # Validate necessary data presence
        if '收盘价' not in df.columns or df['收盘价'].isnull().all():
            print(f"Warning for {stock_code}: '收盘价' (Closing Price) data is missing or all NaN. Skipping RSI calculation.")
            continue
        if len(df) < RSI_PERIOD:
            print(f"Warning for {stock_code}: Insufficient data to calculate RSI for period {RSI_PERIOD} (have {len(df)} rows). Skipping.")
            continue

        # Calculate RSI using the defined function
        df['RSI'] = calculate_rsi(df, period=RSI_PERIOD)

        # Get the latest RSI value
        if df['RSI'].empty or pd.isna(df['RSI'].iloc[-1]):
            print(f"Warning for {stock_code}: RSI calculation resulted in NaN or empty series. Last RSI value is unavailable.")
            continue
        
        last_rsi_value = df['RSI'].iloc[-1]

        # Print the latest RSI value
        print(f"{stock_code}: Latest RSI ({RSI_PERIOD}-day) = {last_rsi_value:.2f}")

        # Check if the latest RSI value meets the overbought threshold
        if last_rsi_value > RSI_OVERBOUGHT_THRESHOLD:
            print(f"ALERT: {stock_code} RSI ({last_rsi_value:.2f}) is above the threshold of {RSI_OVERBOUGHT_THRESHOLD}.")
        else:
            print(f"{stock_code} RSI ({last_rsi_value:.2f}) is not above the threshold.")

    except FileNotFoundError:
        print(f"Error: Data file not found for {stock_code} at '{csv_file_path}'. Please ensure `fetch_stock_data.py` has been run.")
    except Exception as e:
        # Catch any other unexpected errors during processing for a specific stock
        print(f"An unexpected error occurred while processing {stock_code}: {e}")
    
    print("-" * 30) # Separator for readability

print("\nRSI calculation process completed for all specified stocks.")
