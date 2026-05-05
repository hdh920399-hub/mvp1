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

    # 显示扫描到的币种及评分（调试用）
    debug_info = []
    for _, row in ranking_df.iterrows():
        symbol = row["币種"] + "USDT"
        df = get_klines(symbol, "1h", limit=50)
        if df is not None and len(df) >= 30:
            sig = calculate_directional_signal(df)
            long_score = sig["long_score"]
            short_score = sig["short_score"]
            debug_info.append(f"{symbol} 多:{long_score} 空:{short_score}")
        else:
            debug_info.append(f"{symbol} 数据不足")
    st.toast("🔍 扫描结果: " + " | ".join(debug_info[:5]))  # 只显示前5个

    # 按做多分排序
    signals = []
    for _, row in ranking_df.iterrows():
        symbol = row["币種"] + "USDT"
        df = get_klines(symbol, "1h", limit=50)
        if df is not None and len(df) >= 30:
            sig = calculate_directional_signal(df)
            signals.append({
                "symbol": symbol,
                "price": row["价格"],
                "long_score": sig["long_score"],
                "short_score": sig["short_score"],
                "rsi": sig["rsi"]
            })
        else:
            signals.append({
                "symbol": symbol,
                "price": row["价格"],
                "long_score": 0,
                "short_score": 0,
                "rsi": 50
            })

    signals.sort(key=lambda x: x["long_score"], reverse=True)

    for sig in signals:
        if sig["symbol"] in trader.holdings:
            continue
        if sig["long_score"] >= min_score:
            capital = trader.balance
            usdt_amount = max(5, capital * risk_pct)
            success, msg = trader.buy(sig["symbol"], sig["price"], usdt_amount, leverage=1)
            if success:
                result["trades"].append({
                    "action": "BUY",
                    "symbol": sig["symbol"],
                    "price": sig["price"],
                    "amount": usdt_amount
                })
                st.toast(f"✅ 自动开多 {sig['symbol']} @ {sig['price']:.6f}，金额 {usdt_amount:.2f} USDT")
                break
        elif sig["short_score"] >= min_score:
            capital = trader.balance
            usdt_amount = max(5, capital * risk_pct)
            success, msg = trader.short(sig["symbol"], sig["price"], usdt_amount, leverage=1)
            if success:
                result["trades"].append({
                    "action": "SHORT",
                    "symbol": sig["symbol"],
                    "price": sig["price"],
                    "amount": usdt_amount
                })
                st.toast(f"✅ 自动开空 {sig['symbol']} @ {sig['price']:.6f}，金额 {usdt_amount:.2f} USDT")
                break

    if not result["trades"]:
        st.toast("🤖 未发现符合开仓条件的币种（评分均低于阈值）")
    return result
