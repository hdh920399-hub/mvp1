from data.binance import get_klines, get_all_hot_symbols
from engine.ai_signals import calculate_directional_signal


def auto_trade(trader, max_price=1.0, max_positions=3, risk_pct=0.1, min_score=55):
    """基于AI信号自动开仓，返回成交列表。"""
    symbols = get_all_hot_symbols(limit=100)
    trades = []

    current_positions = len(trader.holdings)
    available_slots = max(0, max_positions - current_positions)
    if available_slots <= 0:
        return {"trades": [], "message": "已达到最大持仓数"}

    for symbol in symbols:
        if available_slots <= 0:
            break
        if symbol in trader.holdings:
            continue

        df = get_klines(symbol, "1h", limit=120)
        if df is None or len(df) < 60:
            continue

        last_price = df["close"].iloc[-1]
        if last_price > max_price:
            continue

        signal = calculate_directional_signal(df)
        action = None
        score = 0
        if signal["long_score"] >= min_score:
            action = "BUY"
            score = signal["long_score"]
        elif signal["short_score"] >= min_score:
            action = "SHORT"
            score = signal["short_score"]

        if not action:
            continue

        usdt_amount = max(5, trader.balance * risk_pct)
        if usdt_amount > trader.balance:
            usdt_amount = trader.balance
        if usdt_amount < 5:
            break

        if action == "BUY":
            ok, msg = trader.buy(symbol, last_price, usdt_amount, leverage=1)
        else:
            ok, msg = trader.short(symbol, last_price, usdt_amount, leverage=1)

        if ok:
            trades.append({"action": action, "symbol": symbol, "price": last_price, "score": score})
            available_slots -= 1

    return {"trades": trades, "message": f"本次自动交易完成，成交 {len(trades)} 笔"}
