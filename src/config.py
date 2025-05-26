# config.py
"""
存储应用程序的配置变量。

该文件集中管理API端点等设置或其他全局参数，
这些参数可能需要调整而无需修改应用程序的核心逻辑。
"""

# EASTMONEY_HISTORY_API_URL 是从东方财富服务获取历史K线数据的API端点。
EASTMONEY_HISTORY_API_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"