
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

def get_stock_data(symbol: str, period: str = "1y"):
    """
    獲取單個股票數據
    """
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)

        if hist.empty:
            st.error(f"無法獲取股票 {symbol} 的歷史數據")
            return None, None

        info = stock.info if hasattr(stock, 'info') else {}

        # 確保 info 是字典類型
        if info is None:
            info = {}

        return hist, info
    except Exception as e:
        st.error(f"獲取股票 {symbol} 數據時發生錯誤: {str(e)}")
        return None, None

def get_multiple_stocks_data(symbols: list, period: str = "1y"):
    """
    獲取多個股票的數據
    """
    all_data = {}
    all_info = {}

    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            if not hist.empty:
                all_data[symbol] = hist
                all_info[symbol] = stock.info if hasattr(stock, 'info') else {}
            else:
                st.warning(f"無法獲取股票 {symbol} 的歷史數據")
        except Exception as e:
            st.error(f"獲取股票 {symbol} 數據時發生錯誤: {str(e)}")

    return all_data, all_info

def normalize_stock_prices(stock_data_dict, method='percent'):
    """
    標準化股票價格，用於比較不同價位的股票
    method: 'percent' 表示百分比變化, 'z-score' 表示Z分數標準化
    """
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

def calculate_correlation_matrix(data_dict):
    """
    計算股票之間的相關性矩陣
    """
    close_prices = pd.DataFrame()
    for symbol, data in data_dict.items():
        close_prices[symbol] = data['Close']

    return close_prices.corr()

def get_basic_metrics(info):
    """
    獲取基本財務指標
    """
    def format_number(number):
        """
        格式化數字顯示
        """
        if number is None:
            return "N/A"
        if isinstance(number, str):
            return number
        if number >= 1_000_000_000:
            return f"{number/1_000_000_000:.2f}B"
        if number >= 1_000_000:
            return f"{number/1_000_000:.2f}M"
        if number >= 1_000:
            return f"{number/1_000:.2f}K"
        return f"{number:.2f}"

    # 確保 info 是字典類型
    if info is None:
        info = {}

    metrics = {
        "市值": info.get("marketCap"),
        "本益比": info.get("trailingPE"),
        "股價淨值比": info.get("priceToBook"),
        "每股盈餘": info.get("trailingEps"),
        "殖利率": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
        "交易量": info.get("volume"),
    }
    return {k: format_number(v) for k, v in metrics.items()}
