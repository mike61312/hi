
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import get_multiple_stocks_data, normalize_stock_prices, calculate_correlation_matrix

# 設置頁面配置
st.set_page_config(
    page_title="股票比較分析",
    page_icon="📊",
    layout="wide"
)

# 頁面標題
st.title("📊 股票比較分析")

# 側邊欄設置
with st.sidebar:
    st.subheader("股票選擇")
    
    # 動態添加股票輸入
    stock_inputs = []
    
    stock1 = st.text_input(
        "股票1 (必填)",
        placeholder="例如：AAPL",
        key="stock1"
    )
    stock_inputs.append(stock1)
    
    # 動態添加更多股票
    num_stocks = st.number_input(
        "額外要比較的股票數量",
        min_value=1,
        max_value=5,
        value=2
    )
    
    for i in range(2, num_stocks + 2):
        stock = st.text_input(
            f"股票{i}",
            placeholder=f"例如：MSFT",
            key=f"stock{i}"
        )
        stock_inputs.append(stock)
    
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
        "時間範圍",
        options=list(period_options.keys()),
        index=3  # 默認選擇1年
    )
    
    # 分析類型
    st.subheader("分析設置")
    analysis_type = st.selectbox(
        "分析類型",
        options=["價格走勢", "相對表現", "相關性分析", "波動度比較"],
        index=0
    )
    
    # 標準化方法（僅用於相對表現）
    if analysis_type == "相對表現":
        normalization_method = st.selectbox(
            "標準化方法",
            options=["百分比變化", "Z分數"],
            index=0
        )
    
# 主要內容
if stock1:  # 確保至少輸入了一支股票
    # 過濾掉空白輸入
    stock_symbols = [s.strip() for s in stock_inputs if s.strip()]
    
    if len(stock_symbols) > 0:
        # 獲取股票數據
        with st.spinner("獲取股票數據中..."):
            stock_data, stock_info = get_multiple_stocks_data(stock_symbols, period_options[selected_period])
        
        if stock_data and len(stock_data) > 0:
            # 顯示公司名稱和基本信息
            st.subheader("所選股票:")
            cols = st.columns(len(stock_data))
            for i, (symbol, data) in enumerate(stock_data.items()):
                info = stock_info.get(symbol, {})
                company_name = info.get('longName', symbol)
                current_price = info.get('regularMarketPrice', "N/A")
                change_pct = info.get('regularMarketChangePercent', "N/A")
                
                with cols[i]:
                    st.metric(
                        label=company_name,
                        value=f"${current_price:.2f}" if isinstance(current_price, (int, float)) else current_price,
                        delta=f"{change_pct:.2f}%" if isinstance(change_pct, (int, float)) else change_pct
                    )
            
            # 根據所選分析類型顯示不同的圖表
            if analysis_type == "價格走勢":
                st.subheader("價格走勢比較")
                
                fig = go.Figure()
                
                for symbol, data in stock_data.items():
                    fig.add_trace(go.Scatter(
                        x=data.index,
                        y=data["Close"],
                        name=symbol,
                        mode="lines"
                    ))
                
                fig.update_layout(
                    title="收盤價走勢",
                    xaxis_title="日期",
                    yaxis_title="價格",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 顯示走勢摘要
                st.subheader("走勢摘要")
                
                summary_data = []
                for symbol, data in stock_data.items():
                    first_price = data["Close"].iloc[0]
                    last_price = data["Close"].iloc[-1]
                    price_change = ((last_price / first_price) - 1) * 100
                    highest_price = data["High"].max()
                    lowest_price = data["Low"].min()
                    
                    summary_data.append({
                        "股票": symbol,
                        "起始價": f"${first_price:.2f}",
                        "最終價": f"${last_price:.2f}",
                        "變化 (%)": f"{price_change:.2f}%",
                        "最高價": f"${highest_price:.2f}",
                        "最低價": f"${lowest_price:.2f}"
                    })
                
                st.table(pd.DataFrame(summary_data))
                
            elif analysis_type == "相對表現":
                st.subheader("相對表現比較")
                
                # 標準化股票價格
                method = "percent" if normalization_method == "百分比變化" else "z-score"
                normalized_data = normalize_stock_prices(stock_data, method=method)
                
                fig = go.Figure()
                
                for symbol, values in normalized_data.items():
                    fig.add_trace(go.Scatter(
                        x=values.index,
                        y=values,
                        name=symbol,
                        mode="lines"
                    ))
                
                title = "相對表現 (百分比變化)" if method == "percent" else "相對表現 (Z分數)"
                y_label = "價格變化百分比 (%)" if method == "percent" else "標準差"
                
                fig.update_layout(
                    title=title,
                    xaxis_title="日期",
                    yaxis_title=y_label,
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    template="plotly_white"
                )
                
                if method == "percent":
                    fig.add_shape(
                        type="line",
                        x0=normalized_data[list(normalized_data.keys())[0]].index[0],
                        y0=0,
                        x1=normalized_data[list(normalized_data.keys())[0]].index[-1],
                        y1=0,
                        line=dict(color="black", width=1, dash="dash")
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 績效排名
                st.subheader("績效排名")
                
                performance_data = []
                for symbol, values in normalized_data.items():
                    end_performance = values.iloc[-1]
                    performance_data.append({
                        "股票": symbol,
                        "表現": end_performance,
                        "排名": None  # 稍後填充
                    })
                
                # 排序並添加排名
                performance_df = pd.DataFrame(performance_data)
                performance_df = performance_df.sort_values(by="表現", ascending=False)
                performance_df["排名"] = range(1, len(performance_df) + 1)
                
                # 格式化顯示
                if method == "percent":
                    performance_df["表現"] = performance_df["表現"].apply(lambda x: f"{x:.2f}%")
                else:
                    performance_df["表現"] = performance_df["表現"].apply(lambda x: f"{x:.2f}")
                
                st.table(performance_df)
                
            elif analysis_type == "相關性分析":
                st.subheader("股票間相關性分析")
                
                # 計算相關性矩陣
                corr_matrix = calculate_correlation_matrix(stock_data)
                
                # 創建熱力圖
                fig = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.index,
                    colorscale="RdBu",
                    zmin=-1, zmax=1,
                    colorbar=dict(title="相關係數"),
                    text=np.round(corr_matrix.values, 2),
                    texttemplate="%{text:.2f}"
                ))
                
                fig.update_layout(
                    title="股票收盤價相關性矩陣",
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 相關性解釋
                st.markdown("""
                **相關性解釋:**
                * 1.0: 完全正相關
                * 0.0: 無相關
                * -1.0: 完全負相關
                
                **投資建議:**
                * 高度正相關的股票 (>0.7) 可能具有類似的風險因素
                * 相關性低或負相關的股票 (<0.3) 可能有助於分散投資組合風險
                """)
                
                # 找出最高和最低相關性對
                if len(corr_matrix) > 1:  # 確保至少有兩支股票
                    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
                    upper_tri = corr_matrix.where(mask)
                    
                    # 最高相關性對
                    max_corr = upper_tri.max().max()
                    max_idx = upper_tri.stack().idxmax()
                    
                    # 最低相關性對
                    min_corr = upper_tri.replace(0, np.nan).min().min()
                    min_idx = upper_tri.replace(0, np.nan).stack().idxmin()
                    
                    st.subheader("相關性摘要")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("最高相關性對", f"{max_idx[0]} & {max_idx[1]}", f"{max_corr:.2f}")
                    
                    with col2:
                        st.metric("最低相關性對", f"{min_idx[0]} & {min_idx[1]}", f"{min_corr:.2f}")
                
            elif analysis_type == "波動度比較":
                st.subheader("波動度比較")
                
                # 計算每支股票的波動度 (以標準差衡量)
                volatility_data = []
                
                for symbol, data in stock_data.items():
                    # 計算每日收益率
                    daily_returns = data["Close"].pct_change().dropna()
                    
                    # 計算年化波動度 (標準差 * sqrt(交易日數))
                    annualized_vol = daily_returns.std() * np.sqrt(252) * 100
                    
                    # 計算最大回撤
                    cum_returns = (1 + daily_returns).cumprod()
                    rolling_max = cum_returns.cummax()
                    drawdowns = (cum_returns / rolling_max) - 1
                    max_drawdown = drawdowns.min() * 100
                    
                    volatility_data.append({
                        "股票": symbol,
                        "年化波動度 (%)": annualized_vol,
                        "最大回撤 (%)": max_drawdown
                    })
                
                # 創建波動度圖表
                vol_df = pd.DataFrame(volatility_data)
                
                # 按波動度排序
                vol_df = vol_df.sort_values(by="年化波動度 (%)", ascending=False)
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=vol_df["股票"],
                    y=vol_df["年化波動度 (%)"],
                    name="年化波動度 (%)",
                    marker_color="blue"
                ))
                
                fig.add_trace(go.Bar(
                    x=vol_df["股票"],
                    y=vol_df["最大回撤 (%)"].abs(),  # 取絕對值使正數顯示更直觀
                    name="最大回撤 (%)",
                    marker_color="red"
                ))
                
                fig.update_layout(
                    title="波動度和回撤比較",
                    xaxis_title="股票",
                    barmode="group",
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 顯示波動度數據表
                vol_df["年化波動度 (%)"] = vol_df["年化波動度 (%)"].apply(lambda x: f"{x:.2f}%")
                vol_df["最大回撤 (%)"] = vol_df["最大回撤 (%)"].apply(lambda x: f"{x:.2f}%")
                
                st.table(vol_df)
                
                st.markdown("""
                **波動度解釋:**
                * **年化波動度**: 衡量股票價格波動的激烈程度，數值越高表示風險越大。
                * **最大回撤**: 衡量從最高點到隨後最低點的最大損失，是風險度量的重要指標。
                
                **投資風格:**
                * 保守型投資者可能偏好低波動度的股票
                * 激進型投資者可能接受較高波動度，以期獲得更高回報
                """)
        else:
            st.error("無法獲取所有選定股票的數據，請檢查股票代碼是否正確。")
else:
    st.info("👈 請在左側至少輸入一個股票代碼以開始比較分析")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>數據來源: Yahoo Finance | 使用 Streamlit 開發</p>
    </div>
    """,
    unsafe_allow_html=True
)
