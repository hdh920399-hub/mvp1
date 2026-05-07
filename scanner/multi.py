import pandas as pd
import requests
from engine.multi_factor_score import MultiFactorScorer
from data.binance import get_klines

FUTURES_BASE_URL = "https://fapi.binance.com"

def scan_cheap_coins_with_signal(max_price=1.0, limit=20, offset=0):
    """扫描低价币种，同时计算做多分和做空分"""
    try:
        resp = requests.get(f"{FUTURES_BASE_URL}/fapi/v1/ticker/24hr", 
                           timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code != 200:
            raise Exception(f"API状态码异常: {resp.status_code}")
        data = resp.json()
    except Exception as e:
        raise Exception(f"无法获取币安24h行情数据: {e}")

    cheap = []
    for item in data:
        sym = item["symbol"]
        if not sym.endswith("USDT"):
            continue
        price = float(item["lastPrice"])
        vol = float(item["quoteVolume"])
        if price <= max_price and vol > 50000:
            cheap.append({
                "symbol": sym,
                "price": price,
                "change": float(item["priceChangePercent"]),
                "volume": vol,
                "high": float(item["highPrice"]),
                "low": float(item["lowPrice"])
            })
    if not cheap:
        return pd.DataFrame(), pd.DataFrame(), 0

    cheap.sort(key=lambda x: x["volume"], reverse=True)
    long_results = []
    short_results = []

    for coin in cheap[offset:offset+limit]:
        try:
            symbol = coin["symbol"]
            df = get_klines(symbol, "1h", limit=100)
            if df is None or len(df) < 50:
                continue

            price_now = coin["price"]
            volume_series = df["volume"]

            scorer = MultiFactorScorer(df, price_now, symbol, volume_series, coin["change"])
            # 调用 calculate_scores 返回字典，不是元组
            scores = scorer.calculate_scores()

            long_results.append({
                "币种": symbol.replace("USDT", ""),
                "价格": round(price_now, 6),
                "24h涨跌": f"{coin['change']:+.2f}%",
                "24h量(百万U)": f"{coin['volume']/1e6:.1f}",
                "做多分": scores["long_score"],
                "做多信号": scores["long_signal"],
                "RSI": scores["rsi"],
                "AI分析(多)": scores["long_analysis"]
            })

            short_results.append({
                "币种": symbol.replace("USDT", ""),
                "价格": round(price_now, 6),
                "24h涨跌": f"{coin['change']:+.2f}%",
                "24h量(百万U)": f"{coin['volume']/1e6:.1f}",
                "做空分": scores["short_score"],
                "做空信号": scores["short_signal"],
                "RSI": scores["rsi"],
                "AI分析(空)": scores["short_analysis"]
            })
        except Exception as e:
            print(f"处理 {symbol} 出错: {e}")
            continue

    long_df = pd.DataFrame(long_results).sort_values("做多分", ascending=False) if long_results else pd.DataFrame()
    short_df = pd.DataFrame(short_results).sort_values("做空分", ascending=False) if short_results else pd.DataFrame()
    
    return long_df, short_df, len(cheap)
