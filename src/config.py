# config.py
"""
Stores configuration variables for the application.

This file centralizes settings like API endpoints or other global parameters
that might need to be adjusted without modifying the core logic of the application.
"""

# EASTMONEY_HISTORY_API_URL is the endpoint for fetching historical K-line data
# from Eastmoney's services.
EASTMONEY_HISTORY_API_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"