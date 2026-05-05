import requests
import pandas as pd

BASE = "https://api.binance.com/api/v3"

def get_klines(symbol="BTCUSDT", interval="1h", limit=200):

    url = f"{BASE}/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "t","o","h","l","c","v","ct","q","n","tb","tq","ig"
    ])

    df["open"] = df["o"].astype(float)
    df["high"] = df["h"].astype(float)
    df["low"] = df["l"].astype(float)
    df["close"] = df["c"].astype(float)
    df["volume"] = df["v"].astype(float)

    return df
