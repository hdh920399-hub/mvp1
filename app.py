import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# 导入模块
from data.binance import get_klines, get_symbols
from engine.regime import market_state
from engine.strategies import calculate_signals
from ui.chart import create_candlestick_chart
from risk.position import suggest_position
from scanner.multi import scan_market

# 页面配置
st.set_page_config(page_title="AlphaPilot Lite Pro", layout="wide", page_icon="🚀")

# 标题
st.title("🚀 AlphaPilot Lite Pro - AI 交易分析终端")
st.caption("实时加密货币技术分析 | 数据来自币安公开API")

# ========== 侧边栏配置 ==========
with st.sidebar:
    st.header("⚙️ 配置面板")
    
    symbol = st.selectbox("📊 交易对", get_symbols(), index=0)
    interval = st.selectbox("⏱️ K线周期", ["15m", "1h", "4h", "1d"], index=2)
    lookback = st.slider("📅 数据回看天数", 7, 90, 30)
    
    st.markdown("---")
    capital = st.number_input("💰 本金 (USDT)", min_value=10, value=100, step=10)
    risk_level = st.select_slider("⚠️ 风险偏好", options=["保守", "中", "激进"], value="中")
    
    st.markdown("---")
    if st.button("🔄 刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ========== 主区域 ==========
# 计算时间范围
end_time = datetime.now()
start_time = end_time - timedelta(days=lookback)

# 获取数据
@st.cache_data(ttl=300)
def load_data(sym, interval, lookback_days):
    limit = int(lookback_days * 24 * 4)  # 按4小时估算
    return get_klines(sym, interval, limit=min(limit, 1000))

df = load_data(symbol, interval, lookback)

# 判断数据是否有效
data_valid = df is not None and len(df) >= 20

# 三栏布局
col_chart, col_signals = st.columns([2, 1])

with col_chart:
    st.subheader("📈 价格图表")
    if data_valid:
        fig = create_candlestick_chart(df, symbol)
        st.plotly_chart(fig, use_container_width=True)
        
        # 市场状态
        state = market_state(df)
        state_color = {"BULL": "green", "BEAR": "red", "SIDEWAYS": "orange"}.get(state, "gray")
        st.markdown(f"### 📊 市场状态：**:{state_color}[{state}]**")
    else:
        st.error(f"❌ 无法获取 {symbol} 数据，请检查网络或稍后重试")

with col_signals:
    st.subheader("🧠 AI信号面板")
    if data_valid:
        signals = calculate_signals(df)
        for key, value in signals.items():
            if "🟢" in value:
                st.success(value)
            elif "🔴" in value:
                st.error(value)
            else:
                st.info(value)
        
        st.markdown("---")
        st.subheader("💰 仓位建议")
        position = suggest_position(state, risk_level, capital)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("仓位比例", position["仓位比例"])
        with col2:
            st.metric("杠杆", f"{position['杠杆倍数']}x")
        with col3:
            st.metric("风险", position["风险等级"])
        st.caption(f"{position['仓位金额']} 建议入场")
    else:
        st.warning("等待数据加载...")

# ========== 底部扫描区 ==========
st.markdown("---")
st.subheader("🔥 多币种快速扫描")

with st.spinner("扫描中..."):
    scan_df = scan_market(interval=interval)

if scan_df is not None and not scan_df.empty:
    st.dataframe(scan_df, use_container_width=True)
else:
    st.info("暂无扫描数据")
