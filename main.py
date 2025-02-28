import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from utils.dcf_valuation import calculate_dcf_valuation

# 設置頁面配置
st.set_page_config(
    page_title="股票估值分析",
    page_icon="💰",
    layout="wide"
)

# 標題
st.title("💰 綜合估值分析")

# 側邊欄配置
with st.sidebar:
    st.header("估值設置")
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

    # 相對估值設置
    st.subheader("相對估值設置")
    selected_metrics = st.multiselect(
        "選擇估值指標",
        options=["本益比(P/E)", "股價淨值比(P/B)", "股價營收比(P/S)", "企業價值倍數(EV/EBITDA)"],
        default=["本益比(P/E)", "股價淨值比(P/B)"],
        help="選擇要分析的估值指標"
    )

def calculate_relative_valuation(info):
    """
    計算相對估值指標
    """
    metrics = {}

    if "本益比(P/E)" in selected_metrics:
        pe_ratio = info.get('trailingPE')
        forward_pe = info.get('forwardPE')
        metrics['本益比(P/E)'] = {
            '當前值': pe_ratio,
            '預期值': forward_pe,
            '行業中位數': info.get('industryPE', 'N/A')
        }

    if "股價淨值比(P/B)" in selected_metrics:
        pb_ratio = info.get('priceToBook')
        metrics['股價淨值比(P/B)'] = {
            '當前值': pb_ratio,
            '行業中位數': info.get('industryPB', 'N/A')
        }

    if "股價營收比(P/S)" in selected_metrics:
        ps_ratio = info.get('priceToSalesTrailing12Months')
        metrics['股價營收比(P/S)'] = {
            '當前值': ps_ratio,
            '行業中位數': info.get('industryPS', 'N/A')
        }

    if "企業價值倍數(EV/EBITDA)" in selected_metrics:
        ev_ebitda = info.get('enterpriseToEbitda')
        metrics['企業價值倍數(EV/EBITDA)'] = {
            '當前值': ev_ebitda,
            '行業中位數': info.get('industryEVEBITDA', 'N/A')
        }

    return metrics

def format_value(value):
    """
    格式化數值顯示
    """
    if value is None or value == 'N/A':
        return "N/A"
    if isinstance(value, str):
        return value
    return f"{value:.2f}"

def display_valuation_metrics(metrics):
    """
    顯示估值指標
    """
    for metric_name, values in metrics.items():
        with st.expander(f"{metric_name} 分析"):
            cols = st.columns(len(values))
            for col, (key, value) in zip(cols, values.items()):
                formatted_value = format_value(value)
                col.metric(key, formatted_value)

            # 添加指標說明
            if metric_name == "本益比(P/E)":
                st.info("本益比反映投資人願意為每元盈餘支付的價格，較低的本益比可能代表股票被低估。")
            elif metric_name == "股價淨值比(P/B)":
                st.info("股價淨值比反映投資人願意為每元淨資產支付的價格，較低的股價淨值比可能代表股票具有安全邊際。")
            elif metric_name == "股價營收比(P/S)":
                st.info("股價營收比反映投資人願意為每元營收支付的價格，適合評估尚未獲利的成長型公司。")
            elif metric_name == "企業價值倍數(EV/EBITDA)":
                st.info("企業價值倍數考慮了公司的債務情況，是比較不同資本結構公司的好工具。")

if stock_symbol:
    try:
        # 獲取股票資訊
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        company_name = info.get('longName', stock_symbol)
        current_price = info.get('regularMarketPrice', 0)

        # 顯示公司名稱和當前股價
        st.header(f"{company_name} ({stock_symbol})")
        st.subheader(f"當前股價: ${current_price:.2f}")

        # 創建三個標籤頁
        tab1, tab2, tab3 = st.tabs(["💹 相對估值分析", "💰 DCF估值分析", "📊 財務指標分析"])

        with tab1:
            st.subheader("相對估值分析")
            metrics = calculate_relative_valuation(info)
            display_valuation_metrics(metrics)

        with tab2:
            st.subheader("DCF估值分析")
            # 執行DCF估值
            assumptions, value_per_share = calculate_dcf_valuation(
                stock_symbol,
                forecast_years=forecast_years,
                growth_rate=growth_rate,
                terminal_growth=terminal_growth,
                discount_rate=discount_rate
            )

            if assumptions and value_per_share:
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
                    market_cap = info.get('marketCap', 0)
                    st.metric("市值", f"${market_cap/1e9:.2f}B" if market_cap else "N/A")
                    st.metric("本益比", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A")

                # 顯示估值假設
                st.subheader("估值假設")
                assumptions_df = pd.DataFrame.from_dict(assumptions, orient='index', columns=['值'])
                st.dataframe(assumptions_df)

                # 估值敏感度分析
                st.subheader("估值敏感度分析")
                sensitivity_fig = go.Figure()

                # 生成不同增長率和折現率組合的估值
                growth_rates = [growth_rate-2, growth_rate, growth_rate+2] if growth_rate else [3, 5, 7]
                discount_rates = [discount_rate-2, discount_rate, discount_rate+2]

                for g in growth_rates:
                    values = []
                    for d in discount_rates:
                        assumptions, val = calculate_dcf_valuation(
                            stock_symbol,
                            forecast_years=forecast_years,
                            growth_rate=g,
                            terminal_growth=terminal_growth,
                            discount_rate=d
                        )
                        values.append(val if val else 0)

                    sensitivity_fig.add_trace(go.Scatter(
                        x=discount_rates,
                        y=values,
                        name=f'增長率 {g:.1f}%',
                        mode='lines+markers'
                    ))

                sensitivity_fig.update_layout(
                    title='估值敏感度分析',
                    xaxis_title='折現率 (%)',
                    yaxis_title='估計價值 ($)',
                    template='plotly_white'
                )

                st.plotly_chart(sensitivity_fig, use_container_width=True)

                st.warning("""
                ⚠️ 注意事項：
                1. DCF估值高度依賴於輸入假設，結果可能與實際情況有顯著差異
                2. 建議配合其他分析方法一起使用
                3. 歷史數據不能保證未來表現
                """)
            else:
                st.error("無法計算DCF估值，可能是由於缺少必要的財務數據。")

        with tab3:
            st.subheader("財務指標分析")

            # 獲取財務報表
            income_stmt = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow

            # 計算關鍵財務指標
            if not income_stmt.empty and not balance_sheet.empty:
                # 獲取最近的財務數據
                latest_income = income_stmt.iloc[:,0]
                latest_balance = balance_sheet.iloc[:,0]
                latest_cash_flow = cash_flow.iloc[:,0] if not cash_flow.empty else None

                # 計算財務指標
                financial_metrics = {
                    "獲利能力": {
                        "毛利率": (latest_income.get('Gross Profit', 0) / latest_income.get('Total Revenue', 1)) * 100 if 'Gross Profit' in latest_income else None,
                        "營業利益率": (latest_income.get('Operating Income', 0) / latest_income.get('Total Revenue', 1)) * 100 if 'Operating Income' in latest_income else None,
                        "淨利率": (latest_income.get('Net Income', 0) / latest_income.get('Total Revenue', 1)) * 100 if 'Net Income' in latest_income else None
                    },
                    "償債能力": {
                        "流動比率": latest_balance.get('Total Current Assets', 0) / latest_balance.get('Total Current Liabilities', 1) if 'Total Current Assets' in latest_balance else None,
                        "速動比率": (latest_balance.get('Total Current Assets', 0) - latest_balance.get('Inventory', 0)) / latest_balance.get('Total Current Liabilities', 1) if 'Total Current Assets' in latest_balance else None
                    }
                }

                # 顯示財務指標
                for category, metrics in financial_metrics.items():
                    st.subheader(category)
                    cols = st.columns(len(metrics))
                    for col, (metric_name, value) in zip(cols, metrics.items()):
                        col.metric(
                            metric_name,
                            f"{value:.2f}" if value is not None else "N/A",
                            help=f"最近季度 {metric_name} 數據"
                        )

                # 財務趨勢圖
                st.subheader("財務趨勢分析")
                trend_options = {
                    "收入": income_stmt.loc['Total Revenue'] if 'Total Revenue' in income_stmt.index else None,
                    "淨利": income_stmt.loc['Net Income'] if 'Net Income' in income_stmt.index else None,
                    "營業現金流": cash_flow.loc['Operating Cash Flow'] if not cash_flow.empty and 'Operating Cash Flow' in cash_flow.index else None
                }

                selected_trend = st.selectbox(
                    "選擇要顯示的財務指標",
                    options=list(trend_options.keys())
                )

                if trend_options[selected_trend] is not None:
                    trend_fig = go.Figure()
                    trend_fig.add_trace(go.Bar(
                        x=trend_options[selected_trend].index,
                        y=trend_options[selected_trend].values,
                        name=selected_trend
                    ))

                    trend_fig.update_layout(
                        title=f'{selected_trend}趨勢',
                        xaxis_title='日期',
                        yaxis_title='金額',
                        template='plotly_white'
                    )

                    st.plotly_chart(trend_fig, use_container_width=True)
            else:
                st.warning("無法獲取完整的財務數據。")

    except Exception as e:
        st.error(f"獲取股票數據時發生錯誤: {str(e)}")
else:
    st.info("👈 請在左側輸入股票代碼開始估值分析")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>數據來源: Yahoo Finance | 使用 Streamlit 開發</p>
    </div>
    """,
    unsafe_allow_html=True
)