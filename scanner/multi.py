def scan(symbols, get_df):

    result = []

    for s in symbols:

        df = get_df(s)

        change = df["close"].pct_change().iloc[-1]

        result.append((s, change))

    return sorted(result, key=lambda x: x[1], reverse=True)
