from data.binance import get_klines
from engine.ai_signals import calculate_directional_signal
from scanner.multi import scan_cheap_coins_with_signal
import streamlit as st

def auto_trade(trader, max_price=1.0, max_positions=3, risk_pct=0.1, min_score=55):
    result = {"trades": []}
    if len(trader.holdings) >= max_positions:
        st.toast(f"⚠️ 已达最大持仓数 {max_positions}，暂停自动开仓")
        return result

    ranking_df, _ = scan_cheap_coins_with_signal(max_price=max_price, limit=10, offset=0)
    if ranking_df.empty:
        st.toast("❌ 未扫描到任何低价币")
        return result

    candidates = []
    # 注意：DataFrame 列名为 "币种"（简体）
    for _, row in ranking_df.iterrows():
        symbol = row["币种"] + "USDT"
        df = get_klines(symbol, "1h", limit=50)
        if df is not None and len(df) >= 30:
            sig = calculate_directional_signal(df)
            candidates.append({
                "symbol": symbol,
                "price": row["价格"],
                "net_score": sig["net_score"],
                "long_score": sig["long_score"],
                "short_score": sig["short_score"]
            })
        else:
            candidates.append({
                "symbol": symbol,
                "price": row["价格"],
                "net_score": 0,
                "long_score": 0,
                "short_score": 0
            })

    # 显示前3个币的净得分
    summary = " | ".join([f"{c['symbol']}:净{c['net_score']}" for c in candidates[:3]])
    st.toast(f"🔍 扫描结果: {summary}")

    # 按净得分降序
    candidates.sort(key=lambda x: x["net_score"], reverse=True)

    for c in candidates:
        if c["symbol"] in trader.holdings:
            continue
        if c["net_score"] >= min_score:
            capital = trader.balance
            usdt_amount = max(5, capital * risk_pct)
            success, msg = trader.buy(c["symbol"], c["price"], usdt_amount, leverage=1)
            if success:
                result["trades"].append({
                    "action": "BUY",
                    "symbol": c["symbol"],
                    "price": c["price"],
                    "amount": usdt_amount
                })
                st.toast(f"✅ 自动开多 {c['symbol']} @ {c['price']:.6f} (净得分:{c['net_score']})")
                break
        elif c["net_score"] <= -min_score:
            capital = trader.balance
            usdt_amount = max(5, capital * risk_pct)
            success, msg = trader.short(c["symbol"], c["price"], usdt_amount, leverage=1)
            if success:
                result["trades"].append({
                    "action": "SHORT",
                    "symbol": c["symbol"],
                    "price": c["price"],
                    "amount": usdt_amount
                })
                st.toast(f"✅ 自动开空 {c['symbol']} @ {c['price']:.6f} (净得分:{c['net_score']})")
                break

    if not result["trades"]:
        st.toast("🤖 未发现满足开仓条件的币种（净得分绝对值低于阈值）")
    return result
