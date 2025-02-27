import numpy as np
import pandas as pd
import yfinance as yf

def get_financial_data(symbol: str):
    """
    獲取公司財務數據
    """
    try:
        stock = yf.Ticker(symbol)
        
        # 獲取現金流量表
        cash_flow = stock.cashflow
        # 獲取損益表
        income_stmt = stock.financials
        # 獲取資產負債表
        balance_sheet = stock.balance_sheet
        
        return {
            'cash_flow': cash_flow,
            'income_stmt': income_stmt,
            'balance_sheet': balance_sheet
        }
    except Exception as e:
        return None

def calculate_free_cash_flow(financial_data):
    """
    計算自由現金流
    """
    if financial_data is None:
        return None
    
    try:
        cash_flow = financial_data['cash_flow']
        
        # 獲取營運現金流
        operating_cash_flow = cash_flow.loc['Operating Cash Flow']
        # 獲取資本支出
        capital_expenditure = cash_flow.loc['Capital Expenditure']
        
        # 計算自由現金流
        fcf = operating_cash_flow - abs(capital_expenditure)
        
        return fcf
    except Exception:
        return None

def calculate_growth_rate(data_series):
    """
    計算增長率
    """
    if data_series is None or len(data_series) < 2:
        return None
    
    try:
        # 計算年度增長率
        growth_rates = data_series.pct_change() * 100
        # 計算平均增長率
        avg_growth_rate = growth_rates.mean()
        
        return avg_growth_rate
    except Exception:
        return None

def calculate_dcf_valuation(symbol: str, 
                          forecast_years=5,
                          growth_rate=None,
                          terminal_growth=2.5,
                          discount_rate=10):
    """
    計算DCF估值
    """
    # 獲取財務數據
    financial_data = get_financial_data(symbol)
    if financial_data is None:
        return None, None
    
    # 計算歷史自由現金流
    historical_fcf = calculate_free_cash_flow(financial_data)
    if historical_fcf is None or historical_fcf.empty:
        return None, None
    
    # 如果沒有提供增長率，則計算歷史增長率
    if growth_rate is None:
        growth_rate = calculate_growth_rate(historical_fcf)
        if growth_rate is None:
            growth_rate = 5  # 使用默認增長率
    
    # 使用最新的自由現金流
    latest_fcf = historical_fcf.iloc[0]
    
    # 預測未來現金流
    future_fcf = []
    for year in range(1, forecast_years + 1):
        fcf = latest_fcf * (1 + growth_rate/100) ** year
        future_fcf.append(fcf)
    
    # 計算終值
    terminal_value = (future_fcf[-1] * (1 + terminal_growth/100) / 
                     (discount_rate/100 - terminal_growth/100))
    
    # 折現未來現金流
    discount_factors = [(1 + discount_rate/100) ** -i for i in range(1, forecast_years + 1)]
    pv_fcf = sum(fcf * df for fcf, df in zip(future_fcf, discount_factors))
    
    # 折現終值
    pv_terminal = terminal_value * discount_factors[-1]
    
    # 計算總現值
    total_value = pv_fcf + pv_terminal
    
    # 獲取股票總股數
    shares_outstanding = 0
    try:
        stock_info = yf.Ticker(symbol).info
        # 優先使用流通在外股數 (Shares Outstanding)
        shares_outstanding = stock_info.get('sharesOutstanding', 0)
        
        # 如果無法獲取 sharesOutstanding，嘗試使用其他相關欄位
        if shares_outstanding == 0:
            shares_outstanding = stock_info.get('floatShares', 0)
        
        # 如果還是無法獲取，使用市值除以股價的方法估算
        if shares_outstanding == 0 and 'marketCap' in stock_info and 'regularMarketPrice' in stock_info:
            market_cap = stock_info.get('marketCap', 0)
            price = stock_info.get('regularMarketPrice', 0)
            if price > 0:
                shares_outstanding = market_cap / price
        
        # 計算每股價值
        if shares_outstanding > 0:
            value_per_share = total_value / shares_outstanding
        else:
            value_per_share = None
            
    except Exception as e:
        value_per_share = None
        shares_outstanding = 0
    
    # 準備估值假設
    assumptions = {
        '預測期間': f'{forecast_years}年',
        '增長率': f'{growth_rate:.1f}%',
        '終值增長率': f'{terminal_growth:.1f}%',
        '折現率': f'{discount_rate:.1f}%',
        '最新自由現金流': f'{latest_fcf:,.0f}',
        '預測期間現值': f'{pv_fcf:,.0f}',
        '終值': f'{pv_terminal:,.0f}',
        '總企業價值': f'{total_value:,.0f}',
        '流通在外股數': f'{shares_outstanding:,.0f}' if shares_outstanding > 0 else 'N/A',
        '每股價值': f'{value_per_share:,.2f}' if value_per_share else 'N/A'
    }
    
    return assumptions, value_per_share
