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
        info = stock.info
        return hist, info
    except Exception as e:
        st.error(f"獲取股票數據時發生錯誤: {str(e)}")
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
            info = stock.info
            all_data[symbol] = hist
            all_info[symbol] = info
        except Exception as e:
            st.error(f"獲取股票 {symbol} 數據時發生錯誤: {str(e)}")

    return all_data, all_info

def normalize_stock_prices(data_dict, method='percent'):
    """
    標準化股票價格以便比較
    method: 'percent' 或 'z-score'
    """
    normalized_data = {}

    for symbol, data in data_dict.items():
        if method == 'percent':
            # 轉換為漲跌幅
            first_price = data['Close'].iloc[0]
            normalized_data[symbol] = (data['Close'] - first_price) / first_price * 100
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
    # 創建一個包含所有股票收盤價的DataFrame
    close_prices = pd.DataFrame()
    for symbol, data in data_dict.items():
        close_prices[symbol] = data['Close']

    return close_prices.corr()

def format_number(number):
    """
    格式化數字顯示
    """
    if number is None:
        return "N/A"
    if isinstance(number, (int, float)):
        if number >= 1_000_000_000:
            return f"{number/1_000_000_000:.2f}B"
        if number >= 1_000_000:
            return f"{number/1_000_000:.2f}M"
        if number >= 1_000:
            return f"{number/1_000:.2f}K"
        return f"{number:.2f}"
    return str(number)

def get_basic_metrics(info):
    """
    獲取基本財務指標
    """
    metrics = {
        "市值": info.get("marketCap"),
        "本益比(PE)": info.get("trailingPE"),
        "股息率": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
        "52週最高": info.get("fiftyTwoWeekHigh"),
        "52週最低": info.get("fiftyTwoWeekLow"),
        "交易量": info.get("volume"),
    }
    return {k: format_number(v) for k, v in metrics.items()}

def calculate_ma(data, periods=[5, 20, 60]):
    """
    計算移動平均線
    """
    ma_data = {}
    for period in periods:
        ma_data[f'MA{period}'] = data['Close'].rolling(window=period).mean()
    return ma_data

def calculate_rsi(data, period=14):
    """
    計算RSI指標
    """
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(data, period=20, std_dev=2):
    """
    計算布林通道
    """
    ma = data['Close'].rolling(window=period).mean()
    std = data['Close'].rolling(window=period).std()
    upper_band = ma + (std * std_dev)
    lower_band = ma - (std * std_dev)
    return ma, upper_band, lower_band