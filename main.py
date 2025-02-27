import streamlit as st
import plotly.graph_objects as go
from utils import get_stock_data, get_basic_metrics
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

# 主要內容
if stock_symbol:
    # 獲取股票數據
    hist_data, info = get_stock_data(stock_symbol, period_options[selected_period])
    
    if hist_data is not None and not hist_data.empty:
        # 顯示公司名稱
        company_name = info.get('longName', stock_symbol)
        st.header(f"{company_name} ({stock_symbol})")
        
        # 創建股價圖表
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name='K線圖'
        ))
        
        fig.update_layout(
            title='股票價格走勢',
            yaxis_title='價格',
            xaxis_title='日期',
            template='plotly_white',
            height=600
        )
        
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
