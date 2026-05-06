import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

FUTURES_BASE_URL = "https://fapi.binance.com"

def get_klines(symbol, interval, limit=500):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    url = f"{FUTURES_BASE_URL}/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        resp = session.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
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
        else:
            print(f"状态码异常: {resp.status_code}")
            return None
    except Exception as e:
        print(f"获取K线失败 {symbol}: {e}")
        return None

def get_all_hot_symbols(limit=100):
    url = f"{FUTURES_BASE_URL}/fapi/v1/ticker/24hr"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            usdt_symbols = [item["symbol"] for item in data if item["symbol"].endswith("USDT")]
            usdt_symbols_sorted = sorted(usdt_symbols, key=lambda x: float(next((item["quoteVolume"] for item in data if item["symbol"]==x), 0)), reverse=True)
            return usdt_symbols_sorted[:limit]
    except Exception as e:
        print(f"获取热门币种失败: {e}")
    return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# ---------- 合约数据接口（资金费率、持仓量、多空比） ----------
def get_funding_rate(symbol):
    """获取当前资金费率"""
    url = f"{FUTURES_BASE_URL}/fapi/v1/premiumIndex"
    try:
        resp = requests.get(url, params={"symbol": symbol}, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return float(data.get("lastFundingRate", 0))
    except Exception as e:
        print(f"获取资金费率失败 {symbol}: {e}")
    return 0

# 为了兼容现有代码，添加别名函数 get_current_funding_rate
def get_current_funding_rate(symbol):
    """别名：同 get_funding_rate"""
    return get_funding_rate(symbol)

def get_open_interest(symbol):
    """获取当前持仓量（美元计价）"""
    url = f"{FUTURES_BASE_URL}/fapi/v1/openInterest"
    try:
        resp = requests.get(url, params={"symbol": symbol}, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            oi_usdt = float(data["openInterest"]) * float(data.get("lastPrice", 0))
            return oi_usdt
    except Exception as e:
        print(f"获取持仓量失败 {symbol}: {e}")
    return 0

def get_top_long_short_ratio(symbol):
    """获取顶级账户多空比（账户数多空比）"""
    url = f"{FUTURES_BASE_URL}/futures/data/topLongShortAccountRatio"
    try:
        resp = requests.get(url, params={"symbol": symbol, "period": "5m"}, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[-1].get("longShortRatio", 1.0))
    except Exception as e:
        print(f"获取多空比失败 {symbol}: {e}")
    return 1.0
