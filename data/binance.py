import pandas as pd
import requests
import traceback
import sys

FUTURES_BASE_URL = "https://fapi.binance.com"

def get_klines(symbol, interval, limit=500):
    url = f"{FUTURES_BASE_URL}/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    print(f"尝试获取: {symbol} {interval}")

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"状态码: {resp.status_code}")
        if resp.status_code != 200:
            print(f"错误响应: {resp.text[:200]}")
            return None
        data = resp.json()
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_volume",
            "taker_buy_quote_volume", "ignore"
        ])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        print(f"成功获取 {len(df)} 条数据")
        return df[["time", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"异常: {e}")
        traceback.print_exc()
        return None

def get_all_hot_symbols(limit=100):
    url = f"{FUTURES_BASE_URL}/fapi/v1/ticker/24hr"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            usdt_symbols = [item["symbol"] for item in data if item["symbol"].endswith("USDT")]
            return usdt_symbols[:limit]
    except Exception as e:
        print(f"获取热门币种异常: {e}")
    return ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
