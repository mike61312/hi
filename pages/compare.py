import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils import get_multiple_stocks_data, normalize_stock_prices, calculate_correlation_matrix
import pandas as pd

# 設置頁面配置
st.set_page_config(
    page_title="股票比較分析",
    page_icon="📊",
    layout="wide"
)

# 標題
st.title("📊 股票比較分析")

# 側邊欄配置
with st.sidebar:
    st.header("設置")

    # 多股票輸入
    stocks_input = st.text_area(
        "請輸入股票代碼（每行一個）",
        placeholder="例如：\nAAPL\nMSFT\n2330.TW",
        help="輸入多個股票代碼，每行一個。台股請加上.TW後綴"
    )

    # 時間範圍選擇
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

    # 標準化方法選擇
    normalization_method = st.radio(
        "價格標準化方法",
        options=["原始價格", "漲跌幅(%)", "Z-score標準化"],
        help="選擇不同的標準化方法以便比較不同價格範圍的股票"
    )

# 處理股票代碼輸入
if stocks_input:
    stock_symbols = [symbol.strip() for symbol in stocks_input.split('\n') if symbol.strip()]

    if len(stock_symbols) > 1:
        # 獲取多個股票數據
        all_data, all_info = get_multiple_stocks_data(stock_symbols, period_options[selected_period])

        if all_data:
            # 創建比較圖表
            fig = go.Figure()

            # 根據選擇的標準化方法處理數據
            if normalization_method == "原始價格":
                for symbol, data in all_data.items():
                    fig.add_trace(go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        name=symbol,
                        mode='lines'
                    ))
                y_axis_title = "價格"

            elif normalization_method == "漲跌幅(%)":
                normalized_data = normalize_stock_prices(all_data, method='percent')
                for symbol, prices in normalized_data.items():
                    fig.add_trace(go.Scatter(
                        x=prices.index,
                        y=prices,
                        name=symbol,
                        mode='lines'
                    ))
                y_axis_title = "漲跌幅(%)"

            else:  # Z-score標準化
                normalized_data = normalize_stock_prices(all_data, method='z-score')
                for symbol, prices in normalized_data.items():
                    fig.add_trace(go.Scatter(
                        x=prices.index,
                        y=prices,
                        name=symbol,
                        mode='lines'
                    ))
                y_axis_title = "Z-score"

            # 更新圖表佈局
            fig.update_layout(
                title='股票價格比較',
                yaxis_title=y_axis_title,
                xaxis_title='日期',
                template='plotly_white',
                height=600
            )

            # 顯示比較圖表
            st.plotly_chart(fig, use_container_width=True)

            # 計算並顯示相關性矩陣
            st.subheader("股票相關性分析")
            corr_matrix = calculate_correlation_matrix(all_data)

            # 使用熱力圖顯示相關性
            fig_corr = px.imshow(
                corr_matrix,
                color_continuous_scale='RdBu',
                aspect='auto',
                title='股票相關性熱力圖'
            )

            st.plotly_chart(fig_corr, use_container_width=True)

            # 以簡單的方式顯示相關性數值
            st.dataframe(corr_matrix.round(2))

    else:
        st.warning("請至少輸入兩個股票代碼進行比較")
else:
    st.info("👈 請在左側輸入要比較的股票代碼")

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