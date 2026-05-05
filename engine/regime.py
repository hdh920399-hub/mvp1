def market_state(df):
    # 检查数据量是否足够计算移动平均线
    if len(df) < 50:
        # 数据不足50条时，用简单判断或返回默认状态
        if len(df) > 0:
            last_price = df["close"].iloc[-1]
            first_price = df["close"].iloc[0]
            if last_price > first_price:
                return "BULL"
            elif last_price < first_price:
                return "BEAR"
        return "SIDEWAYS"
    
    # 数据充足时正常计算移动平均线
    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    if ma20 > ma50:
        return "BULL"
    if ma20 < ma50:
        return "BEAR"
    
    return "SIDEWAYS"
