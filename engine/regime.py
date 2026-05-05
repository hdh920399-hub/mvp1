def market_state(df):

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    if ma20 > ma50:
        return "BULL"
    if ma20 < ma50:
        return "BEAR"

    return "SIDEWAYS"
