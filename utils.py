import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

def get_stock_data(symbol: str, period: str = "1y"):
    """
    獲取股票數據
    """
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        info = stock.info
        return hist, info
    except Exception as e:
        st.error(f"獲取股票數據時發生錯誤: {str(e)}")
        return None, None

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
