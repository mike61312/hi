
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from utils import get_stock_data
from utils.technical_indicators import calculate_ma, calculate_rsi, calculate_bollinger_bands

# 設置頁面配置
st.set_page_config(
    page_title="股價模擬與預測",
    page_icon="📈",
    layout="wide"
)

# 頁面標題
st.title("📈 股價模擬與預測")

# 側邊欄設置
with st.sidebar:
    st.header("參數設定")
    
    # 股票設置
    stock_symbol = st.text_input(
        "股票代碼",
        placeholder="例如：AAPL, 2330.TW",
        help="輸入股票代碼，台股請加上.TW後綴"
    )
    
    # 時間範圍
    period_options = {
        "1個月": "1mo",
        "3個月": "3mo",
        "6個月": "6mo",
        "1年": "1y",
        "2年": "2y",
        "5年": "5y"
    }
    selected_period = st.selectbox(
        "歷史數據時間範圍",
        options=list(period_options.keys()),
        index=3  # 默認選擇1年
    )
    
    # 模擬設置
    st.subheader("模擬設置")
    
    simulation_type = st.selectbox(
        "模擬類型",
        options=["蒙特卡洛模擬", "技術指標分析", "支撐阻力分析"],
        index=0
    )
    
    # 模擬參數
    if simulation_type == "蒙特卡洛模擬":
        num_simulations = st.slider(
            "模擬次數",
            min_value=50,
            max_value=1000,
            value=200,
            step=50,
            help="設定進行蒙特卡洛模擬的次數"
        )
        
        forecast_days = st.slider(
            "預測天數",
            min_value=10,
            max_value=252,
            value=30,
            help="設定要預測的天數"
        )
        
        confidence_level = st.slider(
            "信心水平 (%)",
            min_value=50,
            max_value=99,
            value=95,
            help="設定預測區間的信心水平"
        )
    
    elif simulation_type == "技術指標分析":
        # 移動平均線設置
        ma_periods = st.multiselect(
            "移動平均線週期",
            options=[5, 10, 20, 30, 50, 100, 200],
            default=[20, 50, 200],
            help="選擇要顯示的移動平均線週期"
        )
        
        # RSI設置
        show_rsi = st.checkbox("顯示RSI指標", value=True)
        rsi_period = st.slider(
            "RSI週期",
            min_value=7,
            max_value=21,
            value=14,
            help="設定RSI指標的週期"
        )
        
        # 布林帶設置
        show_bollinger = st.checkbox("顯示布林帶", value=True)
        bollinger_period = st.slider(
            "布林帶週期",
            min_value=10,
            max_value=30,
            value=20,
            help="設定布林帶的週期"
        )
        bollinger_std = st.slider(
            "布林帶標準差倍數",
            min_value=1.0,
            max_value=3.0,
            value=2.0,
            step=0.1,
            help="設定布林帶的標準差倍數"
        )
    
    elif simulation_type == "支撐阻力分析":
        # 支撐阻力線設置
        window_size = st.slider(
            "分析窗口大小",
            min_value=5,
            max_value=30,
            value=20,
            help="設定尋找支撐阻力點的窗口大小"
        )
        
        min_touches = st.slider(
            "最小觸及次數",
            min_value=2,
            max_value=5,
            value=3,
            help="設定確認為支撐阻力線的最小觸及次數"
        )

def find_support_resistance_points(data, window=20):
    """
    找出支撐或阻力點
    """
    support_points = []
    resistance_points = []
    
    for i in range(window, len(data) - window):
        # 檢查是否為局部最低點 (支撐點)
        if data['Low'].iloc[i] <= min(data['Low'].iloc[i-window:i]) and \
           data['Low'].iloc[i] <= min(data['Low'].iloc[i+1:i+window+1]):
            support_points.append((data.index[i], data['Low'].iloc[i]))
        
        # 檢查是否為局部最高點 (阻力點)
        if data['High'].iloc[i] >= max(data['High'].iloc[i-window:i]) and \
           data['High'].iloc[i] >= max(data['High'].iloc[i+1:i+window+1]):
            resistance_points.append((data.index[i], data['High'].iloc[i]))
    
    return support_points, resistance_points

def monte_carlo_simulation(data, days, simulations=200, confidence=0.95):
    """
    進行蒙特卡洛模擬
    """
    close_prices = data['Close'].values
    daily_returns = np.log(close_prices[1:] / close_prices[:-1])
    
    # 計算每日回報率的平均值和標準差
    mu = np.mean(daily_returns)
    sigma = np.std(daily_returns)
    
    # 設置模擬參數
    last_price = close_prices[-1]
    simulation_df = pd.DataFrame()
    
    # 進行多次模擬
    for i in range(simulations):
        # 生成隨機每日回報率
        daily_sim_returns = np.random.normal(mu, sigma, days)
        
        # 計算價格路徑
        price_list = [last_price]
        
        for j in daily_sim_returns:
            price_list.append(price_list[-1] * np.exp(j))
        
        # 添加到數據框
        simulation_df[i] = price_list
    
    # 計算信心區間
    sim_data = simulation_df.iloc[-1:].values[0]
    sim_data.sort()
    
    # 計算百分位數
    lower_bound = np.percentile(sim_data, (1 - confidence) * 100 / 2)
    upper_bound = np.percentile(sim_data, 100 - (1 - confidence) * 100 / 2)
    
    return simulation_df, lower_bound, upper_bound

if stock_symbol:
    # 獲取股票數據
    hist_data, info = get_stock_data(stock_symbol, period_options[selected_period])
    
    if hist_data is not None and not hist_data.empty:
        # 顯示公司名稱和當前股價
        company_name = info.get('longName', stock_symbol)
        current_price = info.get('regularMarketPrice', hist_data['Close'].iloc[-1])
        change_pct = info.get('regularMarketChangePercent', 0)
        
        st.header(f"{company_name} ({stock_symbol})")
        st.metric(
            label="當前股價",
            value=f"${current_price:.2f}",
            delta=f"{change_pct:.2f}%" if change_pct else None
        )
        
        # 根據所選的模擬類型顯示不同的結果
        if simulation_type == "蒙特卡洛模擬":
            st.subheader("蒙特卡洛股價模擬")
            
            # 進行蒙特卡洛模擬
            simulation_df, lower_bound, upper_bound = monte_carlo_simulation(
                hist_data, 
                forecast_days, 
                simulations=num_simulations,
                confidence=confidence_level/100
            )
            
            # 創建圖表
            fig = go.Figure()
            
            # 添加歷史價格
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['Close'],
                mode='lines',
                name='歷史收盤價',
                line=dict(color='blue', width=2)
            ))
            
            # 添加模擬軌跡
            for i in range(min(50, num_simulations)):  # 為了視覺清晰，只顯示部分模擬軌跡
                future_dates = [hist_data.index[-1] + timedelta(days=i) for i in range(forecast_days+1)]
                fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=simulation_df[i].values,
                    mode='lines',
                    name=f'模擬 {i}',
                    line=dict(color='rgba(173, 216, 230, 0.2)'),
                    showlegend=False
                ))
            
            # 添加預測區間
            future_dates = [hist_data.index[-1] + timedelta(days=i) for i in range(forecast_days+1)]
            
            # 計算每個時間點的置信區間
            upper_percentile = []
            lower_percentile = []
            median_percentile = []
            
            for i in range(forecast_days+1):
                values_at_time = simulation_df.iloc[i].values
                upper_percentile.append(np.percentile(values_at_time, 100 - (1-confidence_level/100)*100/2))
                lower_percentile.append(np.percentile(values_at_time, (1-confidence_level/100)*100/2))
                median_percentile.append(np.median(values_at_time))
            
            # 添加置信區間
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=upper_percentile,
                mode='lines',
                name=f'上限 ({confidence_level}% 信心區間)',
                line=dict(color='green', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=lower_percentile,
                mode='lines',
                name=f'下限 ({confidence_level}% 信心區間)',
                line=dict(color='red', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=median_percentile,
                mode='lines',
                name='中位數預測',
                line=dict(color='purple', width=2, dash='dash')
            ))
            
            # 更新圖表布局
            fig.update_layout(
                title=f"蒙特卡洛模擬 ({forecast_days}天) - {confidence_level}% 信心區間",
                xaxis_title="日期",
                yaxis_title="股價 ($)",
                hovermode="x unified",
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 顯示模擬結果摘要
            st.subheader("模擬結果摘要")
            
            final_day_results = simulation_df.iloc[-1].values
            expected_return = (np.mean(final_day_results) / current_price - 1) * 100
            
            # 計算風險度量
            var_95 = (current_price - np.percentile(final_day_results, 5)) / current_price * 100  # 95% VaR
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("預期終值", f"${np.mean(final_day_results):.2f}", f"{expected_return:.2f}%")
            
            with col2:
                st.metric(f"{confidence_level}% 區間上限", f"${upper_percentile[-1]:.2f}", f"{(upper_percentile[-1]/current_price-1)*100:.2f}%")
            
            with col3:
                st.metric(f"{confidence_level}% 區間下限", f"${lower_percentile[-1]:.2f}", f"{(lower_percentile[-1]/current_price-1)*100:.2f}%")
            
            # 顯示額外的風險度量
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("風險價值 (95% VaR)", f"{var_95:.2f}%")
            
            with col2:
                win_prob = len(final_day_results[final_day_results > current_price]) / len(final_day_results) * 100
                st.metric("上漲機率", f"{win_prob:.1f}%")
            
            with col3:
                extreme_loss = (current_price - np.percentile(final_day_results, 1)) / current_price * 100  # 99% 極端損失
                st.metric("極端損失風險 (99%)", f"{extreme_loss:.2f}%")
            
            # 模擬參數說明
            st.info(f"""
            **模擬參數說明:**
            - 基於過去 {len(hist_data)} 個交易日的數據
            - 每日回報率均值: {mu*100:.4f}%
            - 每日回報率標準差: {sigma*100:.4f}%
            - 年化波動率: {sigma*np.sqrt(252)*100:.2f}%
            """)
            
            st.warning("""
            **注意事項:**
            1. 模擬結果基於歷史波動性，實際價格可能受到基本面變化、市場情緒等因素影響
            2. 模型假設收益率服從常態分布，但實際市場可能出現極端情況
            3. 預測僅供參考，不應作為投資決策的唯一依據
            """)
        
        elif simulation_type == "技術指標分析":
            st.subheader("技術指標分析")
            
            # 計算技術指標
            # 計算移動平均線
            ma_data = {}
            for period in ma_periods:
                ma_data[f'MA{period}'] = calculate_ma(hist_data, period)
            
            # 計算RSI
            if show_rsi:
                rsi = calculate_rsi(hist_data, rsi_period)
            
            # 計算布林帶
            if show_bollinger:
                upper_band, middle_band, lower_band = calculate_bollinger_bands(
                    hist_data, 
                    bollinger_period, 
                    bollinger_std
                )
            
            # 創建子圖
            fig = make_subplots(
                rows=2, 
                cols=1, 
                shared_xaxes=True,
                vertical_spacing=0.08,
                subplot_titles=("價格與技術指標", "成交量"),
                row_heights=[0.7, 0.3]
            )
            
            # 添加蠟燭圖
            fig.add_trace(
                go.Candlestick(
                    x=hist_data.index,
                    open=hist_data['Open'],
                    high=hist_data['High'],
                    low=hist_data['Low'],
                    close=hist_data['Close'],
                    name="價格"
                ),
                row=1, col=1
            )
            
            # 添加移動平均線
            colors = ['rgba(255,165,0,0.8)', 'rgba(0,255,0,0.8)', 'rgba(255,0,0,0.8)', 
                     'rgba(128,0,128,0.8)', 'rgba(0,128,128,0.8)']
            
            for i, (ma_name, ma_values) in enumerate(ma_data.items()):
                fig.add_trace(
                    go.Scatter(
                        x=hist_data.index,
                        y=ma_values,
                        name=ma_name,
                        line=dict(color=colors[i % len(colors)], width=1.5)
                    ),
                    row=1, col=1
                )
            
            # 添加布林帶
            if show_bollinger:
                fig.add_trace(
                    go.Scatter(
                        x=hist_data.index,
                        y=upper_band,
                        name='上軌',
                        line=dict(color='rgba(173, 204, 255, 0.8)')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=hist_data.index,
                        y=lower_band,
                        name='下軌',
                        line=dict(color='rgba(173, 204, 255, 0.8)'),
                        fill='tonexty',
                        fillcolor='rgba(173, 204, 255, 0.1)'
                    ),
                    row=1, col=1
                )
            
            # 添加成交量
            colors = ['red' if hist_data['Close'].iloc[i] < hist_data['Open'].iloc[i] else 'green'
                     for i in range(len(hist_data))]
            
            fig.add_trace(
                go.Bar(
                    x=hist_data.index,
                    y=hist_data['Volume'],
                    name="成交量",
                    marker=dict(color=colors)
                ),
                row=2, col=1
            )
            
            # 更新圖表布局
            fig.update_layout(
                title=f"{company_name} 技術指標分析",
                xaxis_title="日期",
                yaxis_title="價格 ($)",
                template="plotly_white",
                xaxis_rangeslider_visible=False,
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
            
            # 如果顯示RSI，則添加RSI圖表
            if show_rsi:
                rsi_fig = go.Figure()
                
                rsi_fig.add_trace(go.Scatter(
                    x=hist_data.index,
                    y=rsi,
                    name="RSI",
                    line=dict(color='purple', width=2)
                ))
                
                # 添加超買超賣線
                rsi_fig.add_shape(
                    type="line",
                    x0=hist_data.index[0],
                    y0=70,
                    x1=hist_data.index[-1],
                    y1=70,
                    line=dict(color="red", width=1, dash="dash")
                )
                
                rsi_fig.add_shape(
                    type="line",
                    x0=hist_data.index[0],
                    y0=30,
                    x1=hist_data.index[-1],
                    y1=30,
                    line=dict(color="green", width=1, dash="dash")
                )
                
                # 添加中間線
                rsi_fig.add_shape(
                    type="line",
                    x0=hist_data.index[0],
                    y0=50,
                    x1=hist_data.index[-1],
                    y1=50,
                    line=dict(color="gray", width=1, dash="dash")
                )
                
                rsi_fig.update_layout(
                    title=f"相對強弱指標 (RSI{rsi_period})",
                    xaxis_title="日期",
                    yaxis_title="RSI",
                    yaxis=dict(range=[0, 100]),
                    template="plotly_white"
                )
                
                st.plotly_chart(rsi_fig, use_container_width=True)
                
                # RSI解釋
                st.info("""
                **RSI指標解釋:**
                - RSI > 70: 市場可能超買，存在回調風險
                - RSI < 30: 市場可能超賣，可能出現反彈
                - RSI趨勢線與價格趨勢線發生背離時，可能預示趨勢反轉
                """)
            
            # 顯示技術指標摘要
            st.subheader("技術指標摘要")
            
            # 計算當前技術指標狀態
            current_close = hist_data['Close'].iloc[-1]
            
            # 判斷MA交叉狀態
            ma_status = {}
            for period in sorted(ma_periods):
                current_ma = ma_data[f'MA{period}'].iloc[-1]
                ma_status[f'MA{period}'] = current_ma
                
            # 構建狀態表
            status_data = []
            
            # 價格與MA關係
            for period in sorted(ma_periods):
                current_ma = ma_status[f'MA{period}']
                status = "多頭" if current_close > current_ma else "空頭"
                status_data.append({
                    "指標": f"價格 vs MA{period}",
                    "數值": f"{current_ma:.2f}",
                    "狀態": status
                })
            
            # MA交叉關係
            if len(ma_periods) >= 2:
                ma_periods_sorted = sorted(ma_periods)
                for i in range(len(ma_periods_sorted) - 1):
                    short_period = ma_periods_sorted[i]
                    long_period = ma_periods_sorted[i+1]
                    short_ma = ma_status[f'MA{short_period}']
                    long_ma = ma_status[f'MA{long_period}']
                    
                    if short_ma > long_ma:
                        status = "多頭交叉"
                    else:
                        status = "空頭交叉"
                    
                    status_data.append({
                        "指標": f"MA{short_period} vs MA{long_period}",
                        "數值": f"{short_ma:.2f} vs {long_ma:.2f}",
                        "狀態": status
                    })
            
            # RSI狀態
            if show_rsi:
                current_rsi = rsi.iloc[-1]
                if current_rsi > 70:
                    rsi_status = "超買"
                elif current_rsi < 30:
                    rsi_status = "超賣"
                else:
                    rsi_status = "中性"
                
                status_data.append({
                    "指標": f"RSI ({rsi_period})",
                    "數值": f"{current_rsi:.2f}",
                    "狀態": rsi_status
                })
            
            # 布林帶狀態
            if show_bollinger:
                current_upper = upper_band.iloc[-1]
                current_lower = lower_band.iloc[-1]
                current_middle = middle_band.iloc[-1]
                
                if current_close > current_upper:
                    bb_status = "超過上軌 (超買)"
                elif current_close < current_lower:
                    bb_status = "低於下軌 (超賣)"
                else:
                    # 計算在帶中的位置百分比
                    band_position = (current_close - current_lower) / (current_upper - current_lower) * 100
                    bb_status = f"帶內 ({band_position:.1f}%)"
                
                status_data.append({
                    "指標": "布林帶",
                    "數值": f"{current_lower:.2f} - {current_upper:.2f}",
                    "狀態": bb_status
                })
            
            # 顯示狀態表
            st.table(pd.DataFrame(status_data))
            
            # 技術指標建議
            st.subheader("技術指標建議")
            
            signals = []
            
            # 價格與MA關係
            price_above_ma50 = current_close > ma_status.get('MA50', float('inf'))
            price_above_ma200 = current_close > ma_status.get('MA200', float('inf'))
            
            if 50 in ma_periods and 200 in ma_periods:
                if price_above_ma50 and price_above_ma200:
                    signals.append("價格處於主要均線之上，整體趨勢偏向多頭")
                elif price_above_ma50 and not price_above_ma200:
                    signals.append("價格處於50日均線之上但200日均線之下，中期趨勢偏向多頭但長期趨勢仍有不確定性")
                elif not price_above_ma50 and price_above_ma200:
                    signals.append("價格低於50日均線但高於200日均線，短期可能存在調整，但長期趨勢仍偏向多頭")
                else:
                    signals.append("價格處於主要均線之下，整體趨勢偏向空頭")
            
            # MA交叉
            if 50 in ma_periods and 200 in ma_periods:
                ma50 = ma_status['MA50']
                ma200 = ma_status['MA200']
                
                if ma50 > ma200:
                    signals.append("50日均線位於200日均線之上，形成黃金交叉形態，長期看漲")
                else:
                    signals.append("50日均線位於200日均線之下，形成死亡交叉形態，長期看跌")
            
            # RSI信號
            if show_rsi:
                if current_rsi > 70:
                    signals.append(f"RSI({rsi_period})處於超買區域({current_rsi:.1f})，可能面臨回調風險")
                elif current_rsi < 30:
                    signals.append(f"RSI({rsi_period})處於超賣區域({current_rsi:.1f})，可能出現技術性反彈")
                else:
                    if current_rsi > 50:
                        signals.append(f"RSI({rsi_period})處於中性偏強區域({current_rsi:.1f})")
                    else:
                        signals.append(f"RSI({rsi_period})處於中性偏弱區域({current_rsi:.1f})")
            
            # 布林帶信號
            if show_bollinger:
                if current_close > current_upper:
                    signals.append("價格突破布林帶上軌，呈現強勢，但注意可能超買")
                elif current_close < current_lower:
                    signals.append("價格跌破布林帶下軌，呈現弱勢，但注意可能超賣")
                else:
                    band_width = (current_upper - current_lower) / current_middle * 100
                    if band_width < 10:  # 自定義閾值
                        signals.append(f"布林帶收窄({band_width:.1f}%)，可能即將發生較大行情")
                    else:
                        position = (current_close - current_lower) / (current_upper - current_lower)
                        if position > 0.8:
                            signals.append("價格接近布林帶上軌，上漲動能強")
                        elif position < 0.2:
                            signals.append("價格接近布林帶下軌，下跌壓力大")
                        else:
                            signals.append("價格在布林帶中間區域，趨勢不明確")
            
            # 綜合建議
            for signal in signals:
                st.write(f"- {signal}")
            
            st.warning("""
            **技術分析免責聲明:**
            技術指標僅基於歷史價格數據分析，不考慮基本面因素和外部事件。
            交易決策應結合多種分析方法，並考慮自身風險承受能力。
            """)
        
        elif simulation_type == "支撐阻力分析":
            st.subheader("支撐阻力分析")
            
            # 找出支撐和阻力點
            support_points, resistance_points = find_support_resistance_points(hist_data, window=window_size)
            
            # 創建圖表
            fig = go.Figure()
            
            # 添加蠟燭圖
            fig.add_trace(
                go.Candlestick(
                    x=hist_data.index,
                    open=hist_data['Open'],
                    high=hist_data['High'],
                    low=hist_data['Low'],
                    close=hist_data['Close'],
                    name="價格"
                )
            )
            
            # 添加支撐點
            if support_points:
                dates, values = zip(*support_points)
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=values,
                        mode='markers',
                        marker=dict(
                            color='green',
                            size=8,
                            symbol='triangle-up'
                        ),
                        name="支撐點"
                    )
                )
            
            # 添加阻力點
            if resistance_points:
                dates, values = zip(*resistance_points)
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=values,
                        mode='markers',
                        marker=dict(
                            color='red',
                            size=8,
                            symbol='triangle-down'
                        ),
                        name="阻力點"
                    )
                )
            
            # 尋找可能的支撐阻力線
            if len(support_points) >= min_touches:
                # 按價格分組支撐點
                support_levels = {}
                for date, price in support_points:
                    # 四捨五入到最近的價格區間
                    rounded_price = round(price, 1)  # 可以調整精度
                    if rounded_price not in support_levels:
                        support_levels[rounded_price] = []
                    support_levels[rounded_price].append((date, price))
                
                # 篩選觸及次數達到閾值的支撐線
                valid_support_levels = {p: points for p, points in support_levels.items() if len(points) >= min_touches}
                
                # 繪製支撐線
                for price, points in valid_support_levels.items():
                    dates = [p[0] for p in points]
                    # 計算線的起止日期
                    start_date = hist_data.index[0]
                    end_date = hist_data.index[-1]
                    
                    fig.add_shape(
                        type="line",
                        x0=start_date,
                        y0=price,
                        x1=end_date,
                        y1=price,
                        line=dict(
                            color="green",
                            width=1,
                            dash="dot",
                        ),
                        name=f"支撐線 {price:.2f}"
                    )
            
            if len(resistance_points) >= min_touches:
                # 按價格分組阻力點
                resistance_levels = {}
                for date, price in resistance_points:
                    # 四捨五入到最近的價格區間
                    rounded_price = round(price, 1)  # 可以調整精度
                    if rounded_price not in resistance_levels:
                        resistance_levels[rounded_price] = []
                    resistance_levels[rounded_price].append((date, price))
                
                # 篩選觸及次數達到閾值的阻力線
                valid_resistance_levels = {p: points for p, points in resistance_levels.items() if len(points) >= min_touches}
                
                # 繪製阻力線
                for price, points in valid_resistance_levels.items():
                    dates = [p[0] for p in points]
                    # 計算線的起止日期
                    start_date = hist_data.index[0]
                    end_date = hist_data.index[-1]
                    
                    fig.add_shape(
                        type="line",
                        x0=start_date,
                        y0=price,
                        x1=end_date,
                        y1=price,
                        line=dict(
                            color="red",
                            width=1,
                            dash="dot",
                        ),
                        name=f"阻力線 {price:.2f}"
                    )
            
            # 更新圖表布局
            fig.update_layout(
                title=f"{company_name} 支撐阻力分析",
                xaxis_title="日期",
                yaxis_title="價格 ($)",
                template="plotly_white",
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 顯示支撐阻力水平
            st.subheader("關鍵價格水平")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**潛在阻力線**")
                if len(resistance_points) >= min_touches:
                    valid_resistance_prices = list(sorted([p for p in valid_resistance_levels.keys()]))
                    
                    # 過濾掉當前價格附近的阻力位
                    resistance_above = [p for p in valid_resistance_prices if p > current_price]
                    if resistance_above:
                        nearest_res = min(resistance_above)
                        st.metric(
                            "最近阻力位",
                            f"${nearest_res:.2f}",
                            f"{((nearest_res/current_price) - 1) * 100:.2f}%"
                        )
                        
                        for i, price in enumerate(resistance_above[:3]):
                            st.write(f"{i+1}. ${price:.2f} (+{((price/current_price) - 1) * 100:.2f}%)")
                    else:
                        st.write("未發現當前價格以上的顯著阻力位")
                else:
                    st.write("未發現符合條件的阻力線 (觸及次數不足)")
            
            with col2:
                st.markdown("**潛在支撐線**")
                if len(support_points) >= min_touches:
                    valid_support_prices = list(sorted([p for p in valid_support_levels.keys()], reverse=True))
                    
                    # 過濾掉當前價格以上的支撐位
                    support_below = [p for p in valid_support_prices if p < current_price]
                    if support_below:
                        nearest_sup = max(support_below)
                        st.metric(
                            "最近支撐位",
                            f"${nearest_sup:.2f}",
                            f"{((nearest_sup/current_price) - 1) * 100:.2f}%"
                        )
                        
                        for i, price in enumerate(support_below[:3]):
                            st.write(f"{i+1}. ${price:.2f} ({((price/current_price) - 1) * 100:.2f}%)")
                    else:
                        st.write("未發現當前價格以下的顯著支撐位")
                else:
                    st.write("未發現符合條件的支撐線 (觸及次數不足)")
            
            # 交易區間分析
            if len(support_points) >= min_touches and len(resistance_points) >= min_touches:
                st.subheader("交易區間分析")
                
                # 尋找當前交易區間
                resistance_above = [p for p in valid_resistance_levels.keys() if p > current_price]
                support_below = [p for p in valid_support_levels.keys() if p < current_price]
                
                if resistance_above and support_below:
                    nearest_res = min(resistance_above)
                    nearest_sup = max(support_below)
                    
                    # 計算區間百分比
                    range_pct = (nearest_res - nearest_sup) / nearest_sup * 100
                    position_pct = (current_price - nearest_sup) / (nearest_res - nearest_sup) * 100
                    
                    st.markdown(f"""
                    當前交易區間：**${nearest_sup:.2f} - ${nearest_res:.2f}** (區間大小: {range_pct:.2f}%)  
                    當前價格在區間內的相對位置：**{position_pct:.1f}%**
                    """)
                    
                    # 視覺化交易區間位置
                    progress_html = f"""
                    <div style="width:100%; background-color:#f0f0f0; height:20px; border-radius:5px; margin-bottom:20px;">
                        <div style="width:{position_pct}%; background-color:{'green' if position_pct < 50 else 'orange' if position_pct < 75 else 'red'}; height:100%; border-radius:5px;"></div>
                    </div>
                    """
                    st.markdown(progress_html, unsafe_allow_html=True)
                    
                    # 交易建議
                    if position_pct < 25:
                        st.success("價格接近支撐位，可能是買入機會，風險相對較低")
                    elif position_pct > 75:
                        st.warning("價格接近阻力位，可能面臨壓力，風險相對較高")
                    else:
                        st.info("價格處於區間中段，可考慮等待更好的進場點")
            
            st.warning("""
            **支撐阻力分析免責聲明:**
            - 支撐阻力位是基於歷史價格模式識別的，不保證未來一定有效
            - 支撐阻力可能被突破，尤其是在基本面發生重大變化時
            - 實際交易決策應結合其他分析方法，並設置適當的止損
            """)
    else:
        st.error(f"無法獲取股票 {stock_symbol} 的數據，請檢查股票代碼是否正確")
else:
    st.info("👈 請在左側輸入股票代碼以開始分析")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>數據來源: Yahoo Finance | 使用 Streamlit 開發</p>
    </div>
    """,
    unsafe_allow_html=True
)
