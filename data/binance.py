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

<<<<<<< HEAD
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
=======
def get_symbols():
    """获取热门交易对列表"""
    return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]


def get_all_hot_symbols(limit=100):
    """按成交量获取热门USDT交易对列表"""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        symbols = []
        for item in data:
            sym = item.get("symbol")
            if not sym or not sym.endswith("USDT"):
                continue
            volume = float(item.get("quoteVolume", 0))
            symbols.append((volume, sym))
        symbols.sort(reverse=True)
        return [sym for _, sym in symbols[:limit]]
    except Exception:
        return get_symbols()
>>>>>>> 9b3d143 (更新代码)
