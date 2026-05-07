import pandas as pd
import requests
from engine.multi_factor_score import MultiFactorScorer
from data.binance import get_klines

FUTURES_BASE_URL = "https://fapi.binance.com"

def scan_cheap_coins_with_signal(max_price=1.0, limit=20, offset=0):
    """扫描低价币种，同时计算做多分和做空分"""
    # 获取24h行情数据
    try:
        resp = requests.get(f"{FUTURES_BASE_URL}/fapi/v1/ticker/24hr", 
                           timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code != 200:
            raise Exception(f"API状态码异常: {resp.status_code}")
        data = resp.json()
    except Exception as e:
        raise Exception(f"无法获取币安24h行情数据: {e}")

    # 筛选低价币
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
        return pd.DataFrame(), 0

    cheap.sort(key=lambda x: x["volume"], reverse=True)
    results = []

    for coin in cheap[offset:offset+limit]:
        try:
            symbol = coin["symbol"]
            df = get_klines(symbol, "1h", limit=100)
            if df is None or len(df) < 50:
                continue

            price_now = coin["price"]
            volume_series = df["volume"]

            scorer = MultiFactorScorer(df, price_now, symbol, volume_series, coin["change"])
            # 计算做多分和做空分（返回两个分数）
            long_score, short_score, long_analysis, short_analysis = scorer.calculate_scores()

            results.append({
                "币种": symbol.replace("USDT", ""),
                "价格": round(price_now, 6),
                "24h涨跌": f"{coin['change']:+.2f}%",
                "24h量(百万U)": f"{coin['volume']/1e6:.1f}",
                "做多分": long_score,
                "做空分": short_score,
                "做多信号": "🟢 做多" if long_score >= 60 else "⚪ 弱",
                "做空信号": "🔴 做空" if short_score >= 60 else "⚪ 弱",
                "RSI": scorer.calculate_rsi()[0],
                "AI分析(多)": long_analysis,
                "AI分析(空)": short_analysis
            })
        except Exception as e:
            print(f"处理 {symbol} 出错: {e}")
            continue

    # 分别按做多分和做空分排序
    long_df = pd.DataFrame(results).sort_values("做多分", ascending=False)
    short_df = pd.DataFrame(results).sort_values("做空分", ascending=False)
    
    # 为了兼容旧代码，返回两个DataFrame
    return long_df, short_df, len(cheap)
