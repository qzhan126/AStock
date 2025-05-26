"""
示例脚本：根据存储在CSV文件中的历史数据计算股票的相对强弱指数 (RSI)。

该脚本演示了如何：
- 从JSON文件 ('data/all_stocks.json') 加载股票代码列表。
- 对于每只股票：
    - 从位于 'data/stock_data/' 目录下的CSV文件读取其历史数据。
    - 使用指定的周期（默认为14天）计算RSI。
    - 打印最新的RSI值。
    - 识别并打印RSI值大于70（一个常见的超买信号）的股票。
- 处理潜在错误，如文件丢失或数据问题。
"""
import json
# import csv # 未直接使用，pandas负责CSV读取
import pandas as pd
import numpy as np # 如果扩展，calculate_rsi中用于NaN处理

# --- 配置 ---
DATA_ALL_STOCKS_FILE_PATH = 'data/all_stocks.json'  # 包含股票列表的JSON文件路径
DATA_DIR = 'data/stock_data'             # 存储各个股票CSV文件的目录
RSI_PERIOD = 14                          # RSI计算周期
RSI_OVERBOUGHT_THRESHOLD = 70            # 用于识别超买股票的阈值

# --- RSI计算函数 ---
def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    为给定的数据集计算相对强弱指数 (RSI)。

    :param data: Pandas DataFrame，包含 '收盘价' 列。
    :param period: RSI计算使用的周期（天数）。默认为14。
    :return: Pandas Series，包含RSI值。索引将与输入DataFrame的索引匹配。
             如果找不到 '收盘价' 或计算失败，则返回空的Series。
    """
    if '收盘价' not in data.columns:
        print("错误：DataFrame中未找到 '收盘价' 列。")
        return pd.Series(dtype=float) # 如果缺少必需列，则返回空Series

    delta = data['收盘价'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0 # 上涨部分
    down[down > 0] = 0 # 下跌部分 (以正数表示)

    # 计算指数移动平均 (EMA) 或简单移动平均 (SMA)
    # 此处根据原始简单实现使用SMA：
    avg_gain = up.rolling(window=period, min_periods=1).mean()
    avg_loss = down.abs().rolling(window=period, min_periods=1).mean()
    
    # 计算相对强度 (RS)
    # 如果avg_loss为0，避免除以零；在这种情况下，RSI为100。
    rs = avg_gain / avg_loss
    rs = rs.replace([np.inf, -np.inf], np.nan) # 处理avg_loss最初可能为零的情况
    rs = rs.fillna(method='bfill') # 回填因avg_loss在某些初始周期为0而可能出现的NaN

    # 计算RSI
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # 当avg_loss为0且avg_gain为正时，RSI应为100。
    # 当avg_gain为0且avg_loss为0时，RSI通常被认为是中性的 (例如50或未定义)。
    # 公式 100 - (100 / (1 + RS)) 能正确处理RS -> 无穷大 (avg_loss=0) 的情况，此时RSI -> 100。
    # 如果RS为0 (avg_gain=0, avg_loss > 0)，则RSI为0。
    # 如果两者均为0，RS为NaN，我们已尝试处理。如果RS为0/0 -> NaN，则RSI将为NaN。
    
    return rsi

# --- 主脚本执行 ---

# 加载待处理的股票列表
# 此脚本现在预期 'data/all_stocks.json' 是一个字典列表，
# 每个字典都有 'code' 和 'name' 键。
stock_list_to_process = []
try:
    with open(DATA_ALL_STOCKS_FILE_PATH, 'r', encoding='utf-8') as f:
        stock_list_to_process = json.load(f)
except FileNotFoundError:
    print(f"错误：`{DATA_ALL_STOCKS_FILE_PATH}` 未找到。请先运行 `examples/fetch_stock_data.py` 来生成该文件。")
    exit(1) # 如果主股票列表不可用，则退出
except json.JSONDecodeError:
    print(f"错误：`{DATA_ALL_STOCKS_FILE_PATH}` 文件格式错误，无法解析JSON。")
    exit(1)

# 可选：限制处理的股票数量 (例如，用于测试)
# stock_list_to_process = stock_list_to_process[:5] # 示例：仅处理前5只股票

print(f"开始为 {len(stock_list_to_process)} 只股票计算RSI...\n")

# 遍历每只股票
# stock_info 预期为一个字典，例如 {'code': '000001', 'name': '平安银行'}
for stock_info in stock_list_to_process:
    stock_code = stock_info['code'] # 使用 'code' 键获取文件名和API调用所用的股票代码
    stock_name = stock_info.get('name', stock_code) # 使用 'name' 键获取显示用的股票名称，如果缺失则回退到代码
    
    print(f"--- 正在处理: {stock_name} ({stock_code}) ---")
    
    # 构建股票CSV数据文件的路径（使用股票代码）
    csv_file_path = f'{DATA_DIR}/{stock_code}.csv'
    
    try:
        # 从CSV文件读取历史股票数据
        df = pd.read_csv(csv_file_path, encoding='utf-8')

        # 验证必要数据是否存在
        if '收盘价' not in df.columns or df['收盘价'].isnull().all():
            print(f"警告 {stock_name} ({stock_code}): '收盘价' 数据缺失或全部为NaN。跳过RSI计算。")
            continue
        if len(df) < RSI_PERIOD:
            print(f"警告 {stock_name} ({stock_code}): 数据不足以计算周期为 {RSI_PERIOD} 的RSI (现有 {len(df)} 行)。跳过。")
            continue

        # 使用定义的函数计算RSI
        df['RSI'] = calculate_rsi(df, period=RSI_PERIOD)

        # 获取最新的RSI值
        if df['RSI'].empty or pd.isna(df['RSI'].iloc[-1]):
            print(f"警告 {stock_name} ({stock_code}): RSI计算结果为NaN或空序列。最新的RSI值不可用。")
            continue
        
        last_rsi_value = df['RSI'].iloc[-1]

        # 打印最新的RSI值
        print(f"{stock_name} ({stock_code}): 最新RSI ({RSI_PERIOD}日) = {last_rsi_value:.2f}")

        # 检查最新的RSI值是否达到超买阈值
        if last_rsi_value > RSI_OVERBOUGHT_THRESHOLD:
            print(f"警报: {stock_name} ({stock_code}) RSI ({last_rsi_value:.2f}) 高于阈值 {RSI_OVERBOUGHT_THRESHOLD}。")
        else:
            print(f"{stock_name} ({stock_code}) RSI ({last_rsi_value:.2f}) 未高于阈值。")

    except FileNotFoundError:
        print(f"错误: 未找到 {stock_name} ({stock_code}) 的数据文件于 '{csv_file_path}'。请确保已为该股票运行 `fetch_stock_data.py`。")
    except Exception as e:
        # 捕获处理特定股票时可能发生的任何其他意外错误
        print(f"处理 {stock_name} ({stock_code}) 时发生意外错误: {e}")
    
    print("-" * 30) # 分隔符，提高可读性

print("\n所有指定股票的RSI计算过程已完成。")
