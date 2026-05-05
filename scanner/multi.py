import pandas as pd
from data.binance import get_klines

def scan_market(symbols=None, interval="1h"):
    """扫描多币种"""
    if symbols is None:
        from data.binance import get_symbols
        symbols = get_symbols()
    
    results = []
    for sym in symbols:
        df = get_klines(sym, interval, limit=50)
        if df is not None and len(df) >= 20:
            price = df["close"].iloc[-1]
            change = (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100
            results.append({
                "币种": sym,
                "价格": f"{price:.2f}",
                "24h涨跌": f"{change:+.2f}%"
            })
    
    df_result = pd.DataFrame(results)
    return df_result
