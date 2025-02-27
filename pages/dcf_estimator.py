
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from utils.dcf_valuation import calculate_dcf_valuation

# 設置頁面配置
st.set_page_config(
    page_title="DCF估值計算器",
    page_icon="💲",
    layout="wide"
)

# 標題
st.title("💲 DCF估值計算器")
st.write("使用現金流折現法(DCF)估算股票的合理價格")

# 側邊欄配置
with st.sidebar:
    st.header("估值參數設置")
    stock_symbol = st.text_input(
        "請輸入股票代碼",
        placeholder="例如：AAPL, 2330.TW",
        help="輸入股票代碼，台股請加上.TW後綴"
    )

    # DCF模型參數
    st.subheader("DCF模型參數")
    forecast_years = st.slider(
        "預測年數",
        min_value=3,
        max_value=10,
        value=5,
        help="設置未來現金流預測的年數"
    )
    
    growth_rate = st.number_input(
        "年增長率 (%)",
        min_value=-20.0,
        max_value=50.0,
        value=None,
        placeholder="留空將使用歷史數據計算",
        help="設置預測期間的年度增長率，留空將根據歷史數據計算"
    )
    
    terminal_growth = st.slider(
        "永續增長率 (%)",
        min_value=0.0,
        max_value=5.0,
        value=2.5,
        step=0.1,
        help="設置永續期的增長率，通常接近長期經濟增長率"
    )
    
    discount_rate = st.slider(
        "折現率 (%)",
        min_value=5.0,
        max_value=20.0,
        value=10.0,
        step=0.5,
        help="設置現金流折現率，反映投資風險"
    )

# 主內容
if stock_symbol:
    try:
        # 獲取股票基本資訊
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        company_name = info.get('longName', stock_symbol)
        current_price = info.get('regularMarketPrice', 0)
        
        # 顯示公司名稱和當前股價
        st.header(f"{company_name} ({stock_symbol})")
        st.subheader(f"當前股價: ${current_price:.2f}")
        
        # 執行DCF估值計算
        with st.spinner("計算DCF估值中..."):
            assumptions, value_per_share = calculate_dcf_valuation(
                stock_symbol,
                forecast_years=forecast_years,
                growth_rate=growth_rate,
                terminal_growth=terminal_growth,
                discount_rate=discount_rate
            )
        
        if assumptions and value_per_share:
            # 創建兩欄佈局顯示結果
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("估值結果")
                
                # 計算與當前價格的差距百分比
                if current_price > 0:
                    price_gap = (value_per_share / current_price - 1) * 100
                    price_gap_str = f"{price_gap:.1f}% vs 當前價格"
                else:
                    price_gap_str = None
                
                # 顯示估值結果
                st.metric(
                    "估計內在價值",
                    f"${value_per_share:.2f}",
                    price_gap_str
                )
                
                # 顯示估值結論
                if current_price > 0:
                    if value_per_share > current_price * 1.2:
                        st.success("🔥 嚴重低估 - 當前股價遠低於估計內在價值")
                    elif value_per_share > current_price * 1.05:
                        st.success("👍 可能被低估 - 當前股價低於估計內在價值")
                    elif value_per_share * 1.05 > current_price > value_per_share * 0.95:
                        st.info("🎯 接近公平價值 - 當前股價接近估計內在價值")
                    elif value_per_share * 0.8 < current_price < value_per_share * 0.95:
                        st.warning("👎 可能被高估 - 當前股價高於估計內在價值")
                    else:
                        st.error("⚠️ 嚴重高估 - 當前股價遠高於估計內在價值")
            
            with col2:
                st.subheader("市場數據")
                market_cap = info.get('marketCap', 0)
                st.metric("市值", f"${market_cap/1e9:.2f}B" if market_cap else "N/A")
                st.metric("52週最高價", f"${info.get('fiftyTwoWeekHigh', 0):.2f}" if info.get('fiftyTwoWeekHigh') else "N/A")
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
                title="增長率與折現率敏感度分析",
                height=500,
                xaxis_title="折現率 (%)",
                yaxis_title="增長率 (%)",
                xaxis=dict(tickmode="array", tickvals=list(range(len(discount_values))), ticktext=[f"{d}%" for d in discount_values]),
                yaxis=dict(tickmode="array", tickvals=list(range(len(growth_values))), ticktext=[f"{g}%" for g in growth_values])
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 添加說明和警告
            st.info("""
            **關於DCF估值:**
            現金流折現法(DCF)通過預測公司未來的自由現金流，並將這些現金流折現到現在，來估算公司的內在價值。此方法廣泛應用於投資分析。
            """)
            
            st.warning("""
            ⚠️ **注意事項：**
            1. DCF估值高度依賴於輸入假設，結果可能與實際情況有顯著差異
            2. 未來現金流的不確定性越高，估值的可靠性越低
            3. 建議配合其他分析方法一起使用
            4. 此估值僅供參考，不構成投資建議
            """)
            
        else:
            st.error("無法計算DCF估值，可能是由於缺少必要的財務數據。請嘗試其他股票。")
    
    except Exception as e:
        st.error(f"計算過程中發生錯誤: {str(e)}")
        st.info("可能的原因：股票代碼錯誤、財務數據不完整或無法訪問Yahoo Finance。")
else:
    st.info("👈 請在左側輸入股票代碼開始估值計算")

# 頁面底部
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>數據來源: Yahoo Finance | 使用 Streamlit 開發</p>
        <p>DCF模型使用公司的歷史自由現金流、預測增長率及折現率，計算股票的理論內在價值</p>
    </div>
    """,
    unsafe_allow_html=True
)
