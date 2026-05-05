import pandas as pd
import requests

FUTURES_BASE_URL = "https://fapi.binance.com"

def get_klines(symbol, interval, limit=500):
    """获取币安合约K线数据"""
    url = f"{FUTURES_BASE_URL}/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_volume",
            "taker_buy_quote_volume", "ignore"
        ])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df[["time", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        return None

def get_all_hot_symbols(limit=100):
    """获取热门交易对（按24h成交量排序）"""
    url = f"{FUTURES_BASE_URL}/fapi/v1/ticker/24hr"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        # 过滤USDT合约，按成交量排序
        usdt_symbols = [item for item in data if item["symbol"].endswith("USDT")]
        sorted_symbols = sorted(usdt_symbols, key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
        symbols = [item["symbol"] for item in sorted_symbols[:limit]]
        return symbols
    except Exception as e:
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# 兼容旧代码（如果需要 get_top_symbols）
get_top_symbols = get_all_hot_symbols
