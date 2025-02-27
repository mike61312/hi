import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (
    get_stock_data, get_basic_metrics,
    calculate_ma, calculate_rsi, calculate_bollinger_bands
)
import pandas as pd

# 設置頁面配置
st.set_page_config(
    page_title="股票數據分析儀表板",
    page_icon="📈",
    layout="wide"
)

# 標題
st.title("📈 股票數據分析儀表板")

# 側邊欄配置
with st.sidebar:
    st.header("設置")
    stock_symbol = st.text_input(
        "請輸入股票代碼",
        placeholder="例如：AAPL, 2330.TW",
        help="輸入股票代碼，台股請加上.TW後綴"
    )

    period_options = {
        "1個月": "1mo",
        "3個月": "3mo",
        "6個月": "6mo",
        "1年": "1y",
        "2年": "2y",
        "5年": "5y"
    }
    selected_period = st.selectbox(
        "選擇時間範圍",
        options=list(period_options.keys())
    )

    # 技術指標選擇
    st.header("技術指標")
    show_ma = st.multiselect(
        "移動平均線 (MA)",
        options=["MA5", "MA20", "MA60"],
        default=["MA20"]
    )

    show_rsi = st.checkbox("顯示RSI", value=False)
    show_bollinger = st.checkbox("顯示布林通道", value=False)

    # 成交量分析選項
    st.header("成交量分析")
    show_volume = st.checkbox("顯示成交量", value=True)
    volume_ma = st.checkbox("顯示成交量MA", value=False)

# 主要內容
if stock_symbol:
    # 獲取股票數據
    hist_data, info = get_stock_data(stock_symbol, period_options[selected_period])

    if hist_data is not None and not hist_data.empty:
        # 顯示公司名稱
        company_name = info.get('longName', stock_symbol)
        st.header(f"{company_name} ({stock_symbol})")

        # 創建圖表子圖
        fig = go.Figure()
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.2, 0.2]
        )

        # 添加K線圖
        fig.add_trace(
            go.Candlestick(
                x=hist_data.index,
                open=hist_data['Open'],
                high=hist_data['High'],
                low=hist_data['Low'],
                close=hist_data['Close'],
                name='K線圖'
            ),
            row=1, col=1
        )

        # 添加移動平均線
        if show_ma:
            ma_periods = [int(ma.replace("MA", "")) for ma in show_ma]
            ma_data = calculate_ma(hist_data, ma_periods)
            colors = ['rgba(255,82,82,0.8)', 'rgba(66,133,244,0.8)', 'rgba(52,168,83,0.8)']
            for ma, color in zip(show_ma, colors):
                fig.add_trace(
                    go.Scatter(
                        x=hist_data.index,
                        y=ma_data[ma],
                        name=ma,
                        line=dict(color=color, width=1)
                    ),
                    row=1, col=1
                )

        # 添加布林通道
        if show_bollinger:
            ma20, upper, lower = calculate_bollinger_bands(hist_data)
            fig.add_trace(
                go.Scatter(
                    x=hist_data.index,
                    y=upper,
                    name='上軌',
                    line=dict(color='rgba(128,128,128,0.4)', dash='dash'),
                    fill=None
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=hist_data.index,
                    y=lower,
                    name='下軌',
                    line=dict(color='rgba(128,128,128,0.4)', dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(128,128,128,0.1)'
                ),
                row=1, col=1
            )

        # 添加成交量圖表
        if show_volume:
            # 計算漲跌顏色
            colors = ['red' if close > open else 'green'
                     for close, open in zip(hist_data['Close'], hist_data['Open'])]

            fig.add_trace(
                go.Bar(
                    x=hist_data.index,
                    y=hist_data['Volume'],
                    name='成交量',
                    marker_color=colors,
                    opacity=0.5
                ),
                row=2, col=1
            )

            if volume_ma:
                # 添加成交量MA5
                volume_ma5 = hist_data['Volume'].rolling(window=5).mean()
                fig.add_trace(
                    go.Scatter(
                        x=hist_data.index,
                        y=volume_ma5,
                        name='成交量MA5',
                        line=dict(color='rgba(66,133,244,0.8)', width=1)
                    ),
                    row=2, col=1
                )

        # 添加RSI指標
        if show_rsi:
            rsi = calculate_rsi(hist_data)
            fig.add_trace(
                go.Scatter(
                    x=hist_data.index,
                    y=rsi,
                    name='RSI',
                    line=dict(color='purple', width=1)
                ),
                row=3, col=1
            )

            # 添加超買超賣區域
            fig.add_hline(
                y=70,
                line_color='red',
                line_dash='dash',
                line_width=1,
                row=3, col=1
            )
            fig.add_hline(
                y=30,
                line_color='green',
                line_dash='dash',
                line_width=1,
                row=3, col=1
            )

        # 更新圖表佈局
        fig.update_layout(
            title='股票走勢分析',
            yaxis_title='價格',
            xaxis_title='日期',
            template='plotly_white',
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # 更新子圖Y軸標題
        fig.update_yaxes(title_text="價格", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        if show_rsi:
            fig.update_yaxes(title_text="RSI", row=3, col=1)

        # 顯示圖表
        st.plotly_chart(fig, use_container_width=True)

        # 顯示基本指標
        st.subheader("基本財務指標")
        metrics = get_basic_metrics(info)
        cols = st.columns(3)
        for i, (metric, value) in enumerate(metrics.items()):
            with cols[i % 3]:
                st.metric(metric, value)

        # 下載數據按鈕
        st.subheader("下載歷史數據")
        csv = hist_data.to_csv()
        st.download_button(
            label="下載CSV檔案",
            data=csv,
            file_name=f"{stock_symbol}_historical_data.csv",
            mime="text/csv"
        )

    else:
        st.warning("無法獲取股票數據，請確認股票代碼是否正確。")

else:
    st.info("👈 請在左側輸入股票代碼開始分析")

# 頁面底部
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>數據來源: Yahoo Finance | 使用 Streamlit 開發</p>
    </div>
    """,
    unsafe_allow_html=True
)