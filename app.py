import streamlit as st

from data.binance import get_klines
from engine.voting import vote
from engine.regime import market_state
from risk.position import position
from ui.chart import render

st.set_page_config(layout="wide")

st.title("🚀 AlphaPilot Lite Pro")

symbol = st.selectbox("币种", ["BTCUSDT","ETHUSDT","SOLUSDT"])
balance = st.number_input("资金(USDT)", value=100)

df = get_klines(symbol)

signal = vote(df)
state = market_state(df)

pos, lev = position(balance, 0.7)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🧠 信号")
    st.success(signal)

with col2:
    st.subheader("📊 市场状态")
    st.info(state)

with col3:
    st.subheader("💰 仓位")
    st.write({"pos": pos, "lev": lev})

st.subheader("📈 K线图（TradingView风格）")

st.plotly_chart(render(df, signal), use_container_width=True)
