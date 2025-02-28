# 匯入所有工具函數，使它們可以從utils包直接導入

# 技術指標
from utils.technical_indicators import (
    calculate_ma,
    calculate_rsi,
    calculate_bollinger_bands
)

# DCF估值
from utils.dcf_valuation import (
    get_financial_data,
    calculate_free_cash_flow,
    calculate_growth_rate,
    calculate_dcf_valuation
)

# 分析師預測
from utils.analyst_forecasts import display_analyst_forecasts

# 股票數據函數
from utils.stock_data import (
    get_stock_data,
    get_multiple_stocks_data,
    normalize_stock_prices,
    calculate_correlation_matrix,
    get_basic_metrics
)

# 添加缺少的函數
def get_multiple_stocks_data(symbols, period):
    """
    獲取多支股票的數據
    """
    import yfinance as yf
    all_data = {}
    all_info = {}
    
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            if not hist.empty:
                all_data[symbol] = hist
                all_info[symbol] = stock.info
        except Exception:
            pass
            
    return all_data, all_info

def normalize_stock_prices(stock_data_dict, method='percent'):
    """
    標準化股票價格，用於比較不同價位的股票
    method: 'percent' 表示百分比變化, 'z-score' 表示Z分數標準化
    """
    import pandas as pd
    import numpy as np
    
    normalized_data = {}
    
    for symbol, data in stock_data_dict.items():
        if method == 'percent':
            # 百分比變化（相對於起始價格）
            first_price = data['Close'].iloc[0]
            normalized_data[symbol] = (data['Close'] / first_price - 1) * 100
        elif method == 'z-score':
            # Z-score標準化
            mean = data['Close'].mean()
            std = data['Close'].std()
            normalized_data[symbol] = (data['Close'] - mean) / std
    
    return normalized_data

def calculate_correlation_matrix(stock_data_dict):
    """
    計算多支股票收盤價之間的相關性矩陣
    """
    import pandas as pd
    
    # 創建一個DataFrame包含所有股票的收盤價
    close_prices = pd.DataFrame()
    
    for symbol, data in stock_data_dict.items():
        close_prices[symbol] = data['Close']
    
    # 計算Pearson相關係數
    corr_matrix = close_prices.corr(method='pearson')
    
    return corr_matrix