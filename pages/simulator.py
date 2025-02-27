import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from utils import get_stock_data, calculate_ma, calculate_rsi, calculate_bollinger_bands

# 設置頁面配置
st.set_page_config(
    page_title="趨勢預測模擬器",
    page_icon="🎯",
    layout="wide"
)

# 標題
st.title("🎯 互動式股票趨勢預測模擬器")

# 側邊欄配置
with st.sidebar:
    st.header("設置")
    
    # 股票代碼輸入
    stock_symbol = st.text_input(
        "請輸入股票代碼",
        placeholder="例如：AAPL, 2330.TW",
        help="輸入股票代碼，台股請加上.TW後綴"
    )
    
    # 時間範圍選擇
    period_options = {
        "1個月": "1mo",
        "3個月": "3mo",
        "6個月": "6mo",
        "1年": "1y"
    }
    selected_period = st.selectbox(
        "選擇時間範圍",
        options=list(period_options.keys())
    )
    
    # 趨勢線工具選擇
    st.header("趨勢線工具")
    trend_tool = st.radio(
        "選擇趨勢線類型",
        options=["支撐線", "阻力線", "趨勢線"],
        help="選擇要繪製的趨勢線類型"
    )
    
    # 預測設置
    st.header("預測設置")
    prediction_days = st.slider(
        "預測天數",
        min_value=5,
        max_value=30,
        value=10,
        help="設置要預測的天數"
    )
    
    confidence_level = st.slider(
        "信心水平 (%)",
        min_value=50,
        max_value=99,
        value=95,
        help="設置預測區間的信心水平"
    )

# 主要內容
if stock_symbol:
    # 獲取股票數據
    hist_data, info = get_stock_data(stock_symbol, period_options[selected_period])
    
    if hist_data is not None and not hist_data.empty:
        # 顯示公司名稱
        company_name = info.get('longName', stock_symbol)
        st.header(f"{company_name} ({stock_symbol})")
        
        # 創建互動式圖表
        fig = go.Figure()
        
        # 添加K線圖
        fig.add_trace(go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name='K線圖'
        ))
        
        # 計算移動平均線
        ma_data = calculate_ma(hist_data, [20])
        fig.add_trace(go.Scatter(
            x=hist_data.index,
            y=ma_data['MA20'],
            name='MA20',
            line=dict(color='rgba(66,133,244,0.8)', width=1)
        ))
        
        # 添加布林通道
        ma20, upper, lower = calculate_bollinger_bands(hist_data)
        fig.add_trace(go.Scatter(
            x=hist_data.index,
            y=upper,
            name='上軌',
            line=dict(color='rgba(128,128,128,0.4)', dash='dash'),
            fill=None
        ))
        fig.add_trace(go.Scatter(
            x=hist_data.index,
            y=lower,
            name='下軌',
            line=dict(color='rgba(128,128,128,0.4)', dash='dash'),
            fill='tonexty',
            fillcolor='rgba(128,128,128,0.1)'
        ))
        
        # 生成預測日期
        last_date = hist_data.index[-1]
        future_dates = pd.date_range(
            start=last_date,
            periods=prediction_days + 1,
            freq='B'
        )[1:]
        
        # 計算簡單的趨勢預測
        close_prices = hist_data['Close'].values
        days = np.arange(len(close_prices))
        
        # 使用線性回歸進行趨勢預測
        z = np.polyfit(days, close_prices, 1)
        p = np.poly1d(z)
        
        # 生成預測值
        future_days = np.arange(
            len(close_prices),
            len(close_prices) + prediction_days
        )
        predicted_prices = p(future_days)
        
        # 計算預測區間
        sigma = np.std(close_prices - p(days))
        z_score = {
            95: 1.96,
            99: 2.576,
            90: 1.645,
            80: 1.28,
            50: 0.674
        }
        
        confidence = z_score.get(confidence_level, 1.96)
        upper_bound = predicted_prices + confidence * sigma
        lower_bound = predicted_prices - confidence * sigma
        
        # 添加預測線和區間
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predicted_prices,
            name='預測趨勢',
            line=dict(color='rgba(255,82,82,0.8)', width=2, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=upper_bound,
            name=f'{confidence_level}%信心區間',
            line=dict(color='rgba(255,82,82,0.3)', width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=lower_bound,
            name=f'{confidence_level}%信心區間',
            line=dict(color='rgba(255,82,82,0.3)', width=0),
            fill='tonexty',
            fillcolor='rgba(255,82,82,0.1)'
        ))
        
        # 更新圖表佈局
        fig.update_layout(
            title='股票趨勢預測',
            yaxis_title='價格',
            xaxis_title='日期',
            template='plotly_white',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 顯示圖表
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示預測結果分析
        st.subheader("預測結果分析")
        
        # 計算關鍵價格水平
        current_price = close_prices[-1]
        predicted_end_price = predicted_prices[-1]
        price_change = (predicted_end_price - current_price) / current_price * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "預測目標價",
                f"${predicted_end_price:.2f}",
                f"{price_change:.1f}%"
            )
        
        with col2:
            st.metric(
                "上限目標價",
                f"${upper_bound[-1]:.2f}",
                f"+{((upper_bound[-1]-current_price)/current_price*100):.1f}%"
            )
        
        with col3:
            st.metric(
                "下限目標價",
                f"${lower_bound[-1]:.2f}",
                f"{((lower_bound[-1]-current_price)/current_price*100):.1f}%"
            )
        
        # 添加預測說明
        st.info(f"""
        📈 預測分析（{prediction_days}天）:
        - 當前價格: ${current_price:.2f}
        - 預測區間: ${lower_bound[-1]:.2f} ~ ${upper_bound[-1]:.2f}
        - 信心水平: {confidence_level}%
        
        ⚠️ 注意：此預測基於歷史數據趨勢，僅供參考。實際市場走勢可能受多種因素影響而有所不同。
        """)
        
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
