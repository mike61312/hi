
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.dcf_valuation import calculate_dcf_valuation
from utils.analyst_forecasts import display_analyst_forecasts

# 設置頁面配置
st.set_page_config(
    page_title="DCF估值計算器",
    page_icon="💰",
    layout="wide"
)

# 頁面標題
st.title("💰 DCF估值計算")

# 側邊欄參數
with st.sidebar:
    st.header("DCF模型參數")
    
    # 輸入股票代碼
    stock_symbol = st.text_input(
        "股票代碼",
        placeholder="例如：AAPL, 2330.TW",
        help="輸入股票代碼，台股請加上.TW後綴"
    )
    
    # DCF模型設置
    forecast_years = st.slider(
        "預測年數",
        min_value=3,
        max_value=10,
        value=5,
        help="設定未來現金流預測的年數"
    )
    
    growth_rate = st.number_input(
        "年增長率 (%)",
        min_value=-20.0,
        max_value=50.0,
        value=None,
        placeholder="留空將使用歷史數據計算",
        help="設定預測期間的年度增長率，留空將根據歷史數據計算"
    )
    
    terminal_growth = st.slider(
        "永續增長率 (%)",
        min_value=0.0,
        max_value=5.0,
        value=2.5,
        step=0.1,
        help="設定永續期的增長率"
    )
    
    discount_rate = st.slider(
        "折現率 (%)",
        min_value=5.0,
        max_value=20.0,
        value=10.0,
        step=0.5,
        help="設定現金流折現率"
    )

# 主要內容
if stock_symbol:
    try:
        # 獲取股票數據
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        
        # 顯示公司名稱和當前股價
        company_name = info.get('longName', stock_symbol)
        current_price = info.get('regularMarketPrice', 0)
        
        st.header(f"{company_name} ({stock_symbol})")
        st.subheader(f"當前股價: ${current_price:.2f}")
        
        # 顯示分析師預測數據
        display_analyst_forecasts(stock_symbol)
        
        # 執行DCF估值
        assumptions, value_per_share = calculate_dcf_valuation(
            stock_symbol,
            forecast_years=forecast_years,
            growth_rate=growth_rate,
            terminal_growth=terminal_growth,
            discount_rate=discount_rate
        )
        
        if assumptions and value_per_share:
            # 顯示估值結果
            cols = st.columns(3)
            
            with cols[0]:
                st.metric(
                    "估計內在價值",
                    f"${value_per_share:.2f}",
                    f"{((value_per_share/current_price - 1) * 100):.1f}% vs 當前價格" if current_price else None
                )
                
                if current_price:
                    upside = value_per_share / current_price - 1
                    if upside > 0.2:
                        st.success("👍 顯著低估")
                    elif upside > 0:
                        st.success("👍 輕微低估")
                    elif upside > -0.2:
                        st.info("🎯 接近公平價值")
                    else:
                        st.warning("👎 可能高估")
            
            with cols[1]:
                st.metric("當前市價", f"${current_price:.2f}")
                st.metric("52週最高價", f"${info.get('fiftyTwoWeekHigh', 0):.2f}" if info.get('fiftyTwoWeekHigh') else "N/A")
            
            with cols[2]:
                st.metric("潛在上升空間", f"{((value_per_share/current_price - 1) * 100):.1f}%" if current_price else "N/A")
                st.metric("52週最低價", f"${info.get('fiftyTwoWeekLow', 0):.2f}" if info.get('fiftyTwoWeekLow') else "N/A")

            # 顯示詳細的估值假設
            st.subheader("估值假設明細")
            assumptions_df = pd.DataFrame.from_dict(assumptions, orient='index', columns=['值'])
            st.dataframe(assumptions_df)

            # 估值敏感度分析圖表
            st.subheader("估值敏感度分析")

            # 創建敏感度分析表格
            sensitivity_rates = []
            growth_values = [growth_rate-4, growth_rate-2, growth_rate, growth_rate+2, growth_rate+4] if growth_rate else [1, 3, 5, 7, 9]
            discount_values = [discount_rate-4, discount_rate-2, discount_rate, discount_rate+2, discount_rate+4]

            # 創建敏感度熱力圖數據
            z_values = []
            text_values = []

            for g in growth_values:
                temp_row = []
                text_row = []
                for d in discount_values:
                    if g <= d:  # 確保增長率不超過折現率
                        _, val = calculate_dcf_valuation(
                            stock_symbol,
                            forecast_years=forecast_years,
                            growth_rate=g,
                            terminal_growth=terminal_growth,
                            discount_rate=d
                        )
                        if val:
                            temp_row.append(val)
                            # 格式化文本，顯示當前價值與市價的比例
                            if current_price > 0:
                                ratio = val / current_price
                                text_row.append(f"${val:.2f}<br>({ratio:.2f}x)")
                            else:
                                text_row.append(f"${val:.2f}")
                        else:
                            temp_row.append(None)
                            text_row.append("N/A")
                    else:
                        temp_row.append(None)
                        text_row.append("無效")
                z_values.append(temp_row)
                text_values.append(text_row)

            # 創建熱力圖
            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                x=[f"{d}%" for d in discount_values],
                y=[f"{g}%" for g in growth_values],
                hoverongaps=False,
                text=text_values,
                texttemplate="%{text}",
                colorscale="RdBu_r",
                colorbar=dict(title="估計價值($)")
            ))

            # 更新圖表佈局
            fig.update_layout(
                title="增長率 vs 折現率 敏感度分析",
                xaxis_title="折現率 (%)",
                yaxis_title="年增長率 (%)",
                template="plotly_white"
            )

            # 標記當前使用的增長率和折現率值
            growth_idx = growth_values.index(growth_rate) if growth_rate in growth_values else -1
            discount_idx = discount_values.index(discount_rate) if discount_rate in discount_values else -1

            if growth_idx >= 0 and discount_idx >= 0:
                fig.add_shape(
                    type="circle",
                    xref="x", yref="y",
                    x0=discount_idx-0.5, y0=growth_idx-0.5,
                    x1=discount_idx+0.5, y1=growth_idx+0.5,
                    line=dict(color="green", width=2)
                )

            st.plotly_chart(fig, use_container_width=True)

            # 創建折線圖顯示不同增長率下的估值
            st.subheader("不同增長率下的估值")
            
            line_fig = go.Figure()
            
            for g in [growth_rate-4, growth_rate-2, growth_rate, growth_rate+2, growth_rate+4] if growth_rate else [1, 3, 5, 7, 9]:
                values = []
                for d in np.linspace(discount_rate-4, discount_rate+4, 9):
                    if g <= d:  # 確保增長率不超過折現率
                        _, val = calculate_dcf_valuation(
                            stock_symbol,
                            forecast_years=forecast_years,
                            growth_rate=g,
                            terminal_growth=terminal_growth,
                            discount_rate=d
                        )
                        values.append(val if val else None)
                    else:
                        values.append(None)
                
                line_fig.add_trace(go.Scatter(
                    x=np.linspace(discount_rate-4, discount_rate+4, 9),
                    y=values,
                    name=f"增長率 {g:.1f}%",
                    mode="lines+markers"
                ))
            
            # 添加當前價格水平線
            line_fig.add_shape(
                type="line",
                x0=discount_rate-4, y0=current_price,
                x1=discount_rate+4, y1=current_price,
                line=dict(color="red", width=2, dash="dash"),
                name="當前價格"
            )
            
            line_fig.add_annotation(
                x=discount_rate, y=current_price,
                text=f"當前價格: ${current_price:.2f}",
                showarrow=True,
                arrowhead=1
            )
            
            line_fig.update_layout(
                title="不同增長率和折現率組合下的估值",
                xaxis_title="折現率 (%)",
                yaxis_title="估計價值 ($)",
                template="plotly_white",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(line_fig, use_container_width=True)
            
            # 警告訊息
            st.warning("""
            ⚠️ 重要提示：
            1. DCF估值高度依賴於輸入假設，結果僅供參考
            2. 實際投資決策應結合其他分析方法和個人風險承受能力
            3. 歷史增長不能保證未來表現，請謹慎使用
            4. 增長率不應超過折現率，模型不會計算這些無效的組合
            """)
        else:
            st.error("無法計算DCF估值，可能是由於缺少必要的財務數據。")
    except Exception as e:
        st.error(f"處理過程中發生錯誤: {str(e)}")
else:
    st.info("👈 請在左側輸入股票代碼以開始DCF估值分析")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>數據來源: Yahoo Finance | 使用 Streamlit 開發</p>
    </div>
    """,
    unsafe_allow_html=True
)
