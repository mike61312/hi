import yfinance as yf
import pandas as pd
import numpy as npreamlitport
import streamlit as st

def get_analyst_forecasts(symbol):
    """
    獲取分析師對指定股票的預測數據
    Returns:
        dict: 包含分析師預測的字典
    """
    try:
        # 從 yfinance 獲取股票數據
        stock = yf.Ticker(symbol)

        # 獲取分析師目標價
        if hasattr(stock, 'analysis'):
            analysis = stock.analysis
        else:
            analysis = {}

        # 獲取收益預測
        earnings_forecasts = stock.earnings_forecasts if hasattr(stock, 'earnings_forecasts') else None
        earnings_trend = stock.earnings_trend if hasattr(stock, 'earnings_trend') else None

        # 初始化預測數據結構
        forecasts = {
            "eps_estimates": {
                "next_quarter": None,
                "next_year": None,
            },
            "growth_estimates": {
                "next_year": None,
            },
            "target_price": {
                "low": None,
                "mean": None,
                "high": None
            },
            "recommendations": None
        }

        # 從分析數據中提取目標價
        if hasattr(stock, 'info'):
            forecasts["target_price"]["low"] = stock.info.get('targetLowPrice')
            forecasts["target_price"]["mean"] = stock.info.get('targetMeanPrice')
            forecasts["target_price"]["high"] = stock.info.get('targetHighPrice')

        # 從earnings_trend提取EPS預測
        if earnings_trend is not None and not earnings_trend.empty:
            try:
                # 獲取最新的預測數據
                latest_trend = earnings_trend.iloc[0] if len(earnings_trend) > 0 else None
                if latest_trend is not None:
                    # 提取年度預期EPS增長率
                    growth_estimate = latest_trend.get('Growth')
                    if growth_estimate:
                        forecasts["growth_estimates"]["next_year"] = growth_estimate
            except Exception as e:
                st.warning(f"處理盈利趨勢數據時出錯: {str(e)}")

        # 從其他來源嘗試獲取5年預期
        if hasattr(stock, 'info'):
            # 從info中獲取預估EPS (如果有)
            eps_forecast = stock.info.get('forwardEps')
            if eps_forecast:
                forecasts["eps_estimates"]["next_year"] = eps_forecast

                # 獲取當前EPS
                current_eps = stock.info.get('trailingEps')

                # 如果有當前EPS和預測EPS，計算增長率
                if current_eps and current_eps > 0:
                    growth_rate = (eps_forecast / current_eps) - 1
                    forecasts["growth_estimates"]["next_year"] = growth_rate

            # 獲取分析師推薦
            forecasts["recommendations"] = stock.recommendations if hasattr(stock, 'recommendations') else None

        return forecasts

    except Exception as e:
        st.error(f"獲取分析師預測數據時發生錯誤: {str(e)}")
        return None

def display_analyst_forecasts(symbol):
    """
    顯示分析師對指定股票的預測數據
    """
    forecasts = get_analyst_forecasts(symbol)

    if not forecasts:
        st.warning("無法獲取分析師預測數據")
        return

    # 使用expander來顯示分析師預測
    with st.expander("📊 分析師預測 (未來1年)", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("EPS預測")

            # 獲取預測數據
            next_year_eps = forecasts["eps_estimates"]["next_year"]

            # 顯示未來一年EPS預測
            if next_year_eps:
                st.metric("未來一年EPS", f"${next_year_eps:.2f}")

        with col2:
            st.subheader("EPS增長率預測")

            # 獲取增長率預測
            next_year_growth = forecasts["growth_estimates"]["next_year"]

            # 顯示未來一年增長率
            if next_year_growth:
                st.metric("未來一年EPS增長率", f"{next_year_growth*100:.1f}%")

        # 顯示目標價
        st.subheader("目標價預測")

        target_low = forecasts["target_price"]["low"]
        target_mean = forecasts["target_price"]["mean"]
        target_high = forecasts["target_price"]["high"]

        if target_low and target_mean and target_high:
            target_cols = st.columns(3)
            with target_cols[0]:
                st.metric("最低目標價", f"${target_low:.2f}")
            with target_cols[1]:
                st.metric("平均目標價", f"${target_mean:.2f}")
            with target_cols[2]:
                st.metric("最高目標價", f"${target_high:.2f}")
        else:
            st.info("無法獲取分析師目標價預測")

        # 添加資料來源說明
        st.caption("數據來源: Yahoo Finance 分析師預測")
