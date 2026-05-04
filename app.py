import streamlit as st
import requests

st.set_page_config(page_title="Meme Coin Scanner", layout="wide")

st.title("🚀 Meme Coin Scanner")

# 输入地址
contract = st.text_input("输入代币合约地址（Solana / EVM）")

def get_data(addr):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
        res = requests.get(url, timeout=10)
        data = res.json()
        return data
    except Exception as e:
        return None

if contract:
    st.write("正在查询...")

    data = get_data(contract)

    if not data or "pairs" not in data:
        st.error("❌ 未找到数据")
    else:
        pair = data["pairs"][0]

        st.success("✅ 查询成功")

        st.metric("价格", pair.get("priceUsd", "N/A"))
        st.metric("流动性", pair.get("liquidity", {}).get("usd", "N/A"))
        st.metric("24H交易量", pair.get("volume", {}).get("h24", "N/A"))

        st.write("链：", pair.get("chainId"))
        st.write("DEX：", pair.get("dexId"))

        st.write("🔗 链接：")
        st.write(pair.get("url"))
