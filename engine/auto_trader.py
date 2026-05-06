import streamlit as st
from scanner.multi import scan_cheap_coins_with_signal

def auto_trade(trader, max_price=1.0, max_positions=3, risk_pct=0.1, min_score=20):
    result = {"trades": []}
    if len(trader.holdings) >= max_positions:
        st.toast(f"已达最大持仓数 {max_positions}")
        return result

    ranking_df, total = scan_cheap_coins_with_signal(max_price, limit=10)
    if ranking_df.empty:
        st.toast("未扫描到任何低价币")
        return result

    ranking_df = ranking_df.sort_values("评分", ascending=False)
    st.toast(f"扫描到 {len(ranking_df)} 个币，最高评分: {ranking_df.iloc[0]['评分']}")

    for _, row in ranking_df.iterrows():
        symbol = row["币种"] + "USDT"
        score = row["评分"]
        price = row["价格"]
        signal_type = row.get("AI信号", "")
        leverage = row.get("建议杠杆", 1)   # 使用 AI 建议杠杆，默认1

        if symbol in trader.holdings:
            continue

        if score >= min_score:
            usdt_amount = max(5, trader.balance * risk_pct)
            if "超卖" in signal_type or "偏多" in signal_type or score >= 70:
                success, msg = trader.buy(symbol, price, usdt_amount, leverage=leverage)
                action = "BUY"
            elif "超买" in signal_type or "偏空" in signal_type:
                success, msg = trader.short(symbol, price, usdt_amount, leverage=leverage)
                action = "SHORT"
            else:
                continue

            if success:
                result["trades"].append({
                    "action": action,
                    "symbol": symbol,
                    "price": price,
                    "leverage": leverage
                })
                st.toast(f"✅ 自动{action} {symbol} @ {price} (评分:{score}, 杠杆:{leverage}x)")
                return result
    st.toast(f"未找到评分 ≥ {min_score} 的币种")
    return result
