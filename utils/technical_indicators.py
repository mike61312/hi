import pandas as pd
import numpy as np

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
