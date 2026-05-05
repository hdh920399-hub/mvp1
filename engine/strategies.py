def ma_strategy(df):

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    if ma20 > ma50:
        return "BUY"
    if ma20 < ma50:
        return "SELL"
    return "HOLD"


def momentum(df):

    r = df["close"].pct_change().iloc[-1]

    if r > 0.02:
        return "BUY"
    if r < -0.02:
        return "SELL"
    return "HOLD"


def breakout(df):

    if df["close"].iloc[-1] > df["high"].rolling(20).max().iloc[-2]:
        return "BUY"

    return "HOLD"
