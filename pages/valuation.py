import streamlit as st
import yfinance as yf
from utils.dcf_valuation import calculate_dcf_valuation

# 設置頁面配置
st.set_page_config(
    page_title="股票估值分析",
    page_icon="💰",
    layout="wide"
)

# 標題
st.title("💰 DCF股票估值分析")

# 側邊欄配置
with st.sidebar:
    st.header("估值設置")
    
    # 股票代碼輸入
    stock_symbol = st.text_input(
        "請輸入股票代碼",
        placeholder="例如：AAPL, 2330.TW",
        help="輸入股票代碼，台股請加上.TW後綴"
    )
    
    # DCF參數設置
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
        help="設置永續期的增長率"
    )
    
    discount_rate = st.slider(
        "折現率 (%)",
        min_value=5.0,
        max_value=20.0,
        value=10.0,
        step=0.5,
        help="設置現金流折現率"
    )

# 主要內容
if stock_symbol:
    # 獲取股票基本信息
    try:
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        company_name = info.get('longName', stock_symbol)
        current_price = info.get('regularMarketPrice', 0)
        
        st.header(f"{company_name} ({stock_symbol})")
        
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
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("估值結果")
                st.metric(
                    "估計內在價值",
                    f"${value_per_share:.2f}",
                    f"{((value_per_share/current_price - 1) * 100):.1f}% vs 當前價格" if current_price else None
                )
                
                if current_price:
                    if value_per_share > current_price:
                        st.success("👍 當前股價可能被低估")
                    elif value_per_share < current_price:
                        st.warning("👎 當前股價可能被高估")
                    else:
                        st.info("🎯 當前股價接近估計價值")
            
            with col2:
                st.subheader("當前市場數據")
                st.metric("當前股價", f"${current_price:.2f}" if current_price else "N/A")
                st.metric("市值", f"${info.get('marketCap', 0)/1e9:.2f}B" if info.get('marketCap') else "N/A")
                st.metric("本益比", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A")
            
            # 顯示估值假設
            st.subheader("估值假設")
            assumptions_df = pd.DataFrame.from_dict(assumptions, orient='index', columns=['值'])
            st.dataframe(assumptions_df)
            
            # 添加警告說明
            st.warning("""
            ⚠️ 注意事項：
            1. DCF估值高度依賴於輸入假設，結果可能與實際情況有顯著差異
            2. 建議配合其他分析方法一起使用
            3. 歷史數據不能保證未來表現
            """)
            
        else:
            st.error("無法計算DCF估值，可能是由於缺少必要的財務數據。")
            
    except Exception as e:
        st.error(f"獲取股票數據時發生錯誤: {str(e)}")
        
else:
    st.info("👈 請在左側輸入股票代碼開始估值分析")

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
