def market_state(df):
    if df is None or len(df) < 20:
        return "UNKNOWN"
    close = df["close"]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
    if ma20 > ma50:
        return "BULL"
    elif ma20 < ma50:
        return "BEAR"
    else:
        return "SIDEWAYS"
