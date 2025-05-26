"""
Example script to fetch historical stock data for a list of stocks
and save it to individual CSV files.

This script demonstrates how to:
- Load a list of stock codes from a JSON file ('data/all_stocks.json').
- Iterate through each stock code.
- Call the `fetch_stock_history` function from `src.api_client` to get K-line data.
- Process the returned data.
- Save the K-line data to a CSV file in the 'data/stock_data/' directory
  using the `save_to_csv` function and `KLINE_CSV_HEADER` from `src.utils`.
- Handle potential errors during fetching or file operations.
- Includes an optional delay between API calls to be respectful to the server.
"""
import json
import os
import time # For adding delays between API calls
# import pandas as pd # Not directly used in this script after refactoring
# import numpy as np # Not used
# import requests # Now handled by api_client
# import re # Now handled by api_client
# import csv # Now handled by utils.save_to_csv

from src.api_client import fetch_stock_history
from src.utils import save_to_csv, KLINE_CSV_HEADER


# --- Configuration ---
STOCK_LIST_FILE = 'data/all_stocks.json' # Path to the JSON file containing the list of stocks
OUTPUT_DIR = 'data/stock_data'          # Directory to save the fetched CSV data
KLINE_TYPE = 101                        # K-line type (101 for daily)
API_DELAY_SECONDS = 1                   # Delay in seconds between API calls

# --- Main script execution ---

# Load the list of stocks to process
# This script expects 'data/all_stocks.json' to be a list of objects,
# where each object has a 'stock_code' key.
# Ensure this script is run from the root directory of the project,
# or adjust file paths accordingly.
try:
    with open(STOCK_LIST_FILE, 'r', encoding='utf-8') as f:
        stock_list_full = json.load(f)
except FileNotFoundError:
    print(f"Error: '{STOCK_LIST_FILE}' not found. Make sure the file exists or you are running the script from the project root.")
    stock_list_full = [] # Initialize to empty list to prevent further errors if file not found

# Optional: Limit the number of stocks to process (e.g., for testing)
# stock_list_to_process = stock_list_full[:5] # Example: process only the first 5 stocks
stock_list_to_process = stock_list_full

# Ensure the output directory for stock data exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Created output directory: {OUTPUT_DIR}")

# Iterate through each stock in the list
for stock_info in stock_list_to_process:
    stock_code = stock_info['stock_code']
    print(f"Processing stock: {stock_code}...")
    
    # Define the path for the output CSV file
    csv_file_path = os.path.join(OUTPUT_DIR, f'{stock_code}.csv')

    # Optional: Skip downloading if the CSV file already exists
    if os.path.exists(csv_file_path):
        print(f"Data for {stock_code} already exists at {csv_file_path}. Skipping download.")
        continue

    try:
        # Fetch stock history data using the api_client
        # klt=KLINE_TYPE specifies the K-line period (e.g., daily, weekly)
        history_data_response = fetch_stock_history(stock_code=stock_code, klt=KLINE_TYPE)

        # Process the response
        if history_data_response and history_data_response.get('data') and history_data_response['data'].get('klines'):
            klines_raw_list = history_data_response['data']['klines'] # List of strings, each is a k-line record
            
            if not klines_raw_list:
                print(f"No k-line data found for {stock_code} in the API response (klines list is empty).")
                continue

            # Convert the list of k-line strings into a list of lists (rows for CSV)
            # Each string in klines_raw_list is comma-separated.
            processed_kline_data_for_csv = [kline_record.split(',') for kline_record in klines_raw_list]
            
            # Save the processed data to a CSV file using the utility function
            # KLINE_CSV_HEADER provides the header row for the CSV file.
            save_to_csv(csv_file_path, processed_kline_data_for_csv, KLINE_CSV_HEADER)
            print(f"Successfully fetched and saved data for {stock_code} to {csv_file_path}")

        # Handle cases where the API might return a success status but no actual 'data' or 'klines'
        elif history_data_response and history_data_response.get('data') is None:
             print(f"Warning: API response for {stock_code} lacks 'data' field, though the request might have been successful. Response: {history_data_response}")
        else:
            # Handle other unsuccessful fetch scenarios or empty data
            print(f"Warning: Failed to fetch data for {stock_code}, or the response did not contain k-line data. Response: {history_data_response}")

        # Implement a delay to be respectful to the API server and avoid rate limiting
        print(f"Waiting for {API_DELAY_SECONDS} second(s) before next request...")
        time.sleep(API_DELAY_SECONDS)

    except Exception as e:
        # Catch any other exceptions that might occur during the process for a specific stock
        print(f"An unexpected error occurred while processing {stock_code}: {e}")
        # Optional: could add stock_code to a list of failed attempts here

print("\nStock data fetching process completed.")
