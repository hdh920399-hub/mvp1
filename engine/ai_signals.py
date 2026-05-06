def calculate_directional_signal(df):
    return {
        "net_score": 0,
        "long_score": 0,
        "short_score": 0,
        "direction": "NEUTRAL",
        "summary": "数据不足",
        "analysis": "等待K线数据",
        "rsi": 50,
        "vol_ratio": 1.0
    }
