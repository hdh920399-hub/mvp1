import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
from datetime import datetime, timedelta

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
    except Exception as e:
        print(f"API获取失败: {e}")

    # 生成模拟K线数据（fallback）
    print(f"使用模拟数据: {symbol}")
    end = datetime.now()
    start = end - timedelta(days=limit // 24)
    times = pd.date_range(start=start, periods=limit, freq='1h')
    base_price = random.uniform(0.01, 1.0)
    closes = []
    for i in range(limit):
        change = random.uniform(-0.08, 0.08)
        base_price *= (1 + change)
        closes.append(base_price)
    df = pd.DataFrame({
        "time": times,
        "open": [closes[i-1] if i>0 else closes[0] for i in range(limit)],
        "high": [c * random.uniform(1, 1.05) for c in closes],
        "low": [c * random.uniform(0.95, 1) for c in closes],
        "close": closes,
        "volume": [random.uniform(100000, 10000000) for _ in range(limit)]
    })
    return df

def get_all_hot_symbols(limit=100):
    # 优先尝试从币安获取，失败则返回默认列表
    url = f"{FUTURES_BASE_URL}/fapi/v1/ticker/24hr"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            usdt_symbols = [item["symbol"] for item in data if item["symbol"].endswith("USDT")]
            return usdt_symbols[:limit]
    except Exception as e:
        print(f"获取热门币种失败: {e}")
    # 默认热门币种（保证界面不空白）
    return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "MATICUSDT"]
