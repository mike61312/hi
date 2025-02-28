
import streamlit as st
import sys
import os

# 添加當前目錄到路徑，確保 Python 能夠找到我們的模塊
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 設置頁面配置
st.set_page_config(
    page_title="股票分析工具集",
    page_icon="📊",
    layout="wide"
)

# 網站主標題及介紹
st.title("📊 股票智能分析平台")
st.markdown("### 全方位的股票分析與估值工具")

# 主要功能介紹
st.markdown("---")

# 三欄布局，顯示主要功能
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 💰 綜合估值分析")
    st.markdown("""
    提供多樣化的估值方法:
    - 相對估值 (P/E, PEG, P/B等)
    - DCF 估值模型
    - 財務指標分析
    """)
    st.markdown("[開始估值分析 →](/股票智能分析平台/估值分析)")

with col2:
    st.markdown("### 💲 DCF估值計算器")
    st.markdown("""
    專業的現金流折現估值工具:
    - 分析師預測整合
    - 敏感度分析
    - 估值結果視覺化
    """)
    st.markdown("[使用DCF估值 →](/股票智能分析平台/DCF估值計算器)")

with col3:
    st.markdown("### 📊 股票比較與趨勢分析")
    st.markdown("""
    比較多支股票表現:
    - 價格趨勢比較
    - 相關性分析
    - 技術指標模擬
    """)
    st.markdown("[開始比較分析 →](/股票智能分析平台/股票比較分析)")

# 使用說明
st.markdown("---")
st.header("如何使用本平台")

st.markdown("""
1. **選擇分析工具**: 從上方或側邊欄選擇您想使用的分析工具
2. **輸入股票代碼**: 輸入您感興趣的股票代碼 (例如: AAPL, 2330.TW)
3. **調整參數**: 根據需要調整分析參數
4. **分析結果**: 查看詳細的分析報告和視覺化圖表
""")

# 資料來源聲明
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>數據來源: Yahoo Finance | 使用 Streamlit 開發</p>
    <p>© 2024 股票智能分析平台</p>
</div>
""", unsafe_allow_html=True)
