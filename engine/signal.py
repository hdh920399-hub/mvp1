def signal_score(df):

    change = df["close"].pct_change().iloc[-1]

    if change > 0.02:
        return "BUY"

    if change < -0.02:
        return "SELL"

    return "HOLD"
