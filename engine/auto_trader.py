import streamlit as st
from scanner.multi import scan_cheap_coins_with_signal

def auto_trade(trader, max_price=1.0, max_positions=3, risk_pct=0.1, min_score=60):
    result = {"trades": []}
    st.toast("自动交易扫描中...")
    return result
