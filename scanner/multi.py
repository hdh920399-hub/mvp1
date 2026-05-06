import pandas as pd
import requests
from data.binance import get_klines

FUTURES_BASE_URL = "https://fapi.binance.com"

def scan_cheap_coins_with_signal(max_price=1.0, limit=20, offset=0):
    url = f"{FUTURES_BASE_URL}/fapi/v1/ticker/24hr"
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        data = resp.json()
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
                    "volume": vol
                })
        cheap.sort(key=lambda x: x["volume"], reverse=True)
        results = []
        for coin in cheap[offset:offset+limit]:
            df = get_klines(coin["symbol"], "1h", limit=60)
            rsi = 50
            signal = "⚪中性"
            score = 50
            analysis = "数据不足，暂用成交量排序"
            if df is not None and len(df) >= 30:
                close = df["close"]
                delta = close.diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(14).mean()
                avg_loss = loss.rolling(14).mean()
                rs = avg_gain / avg_loss
                rsi_val = (100 - (100 / (1 + rs))).iloc[-1]
                rsi = round(rsi_val, 1)
                # 根据 RSI 和 24h 涨跌综合评分
                if rsi < 30:
                    score = 80
                    signal = "🟢超卖"
                    analysis = f"RSI={rsi}（超卖），价格可能反弹，建议关注做多机会。"
                elif rsi < 45:
                    score = 65
                    signal = "🟢偏多"
                    analysis = f"RSI={rsi}（偏低），有上涨潜力，可考虑轻仓试多。"
                elif rsi > 70:
                    score = 20
                    signal = "🔴超买"
                    analysis = f"RSI={rsi}（超买），回调风险增大，不宜追高。"
                elif rsi > 55:
                    score = 35
                    signal = "🔴偏空"
                    analysis = f"RSI={rsi}（偏高），可能面临压力。"
                else:
                    score = 50
                    signal = "⚪中性"
                    analysis = f"RSI={rsi}（中性），无明显倾向，观望为主。"
                # 24h 涨跌幅修正
                chg = coin["change"]
                if chg > 10 and rsi < 50:
                    score = min(95, score + 10)
                    analysis += " 24h 涨幅较大但 RSI 未超买，可能有后续动能。"
                elif chg < -10 and rsi > 50:
                    score = max(5, score - 10)
                    analysis += " 24h 跌幅较大且 RSI 偏高，注意继续下跌风险。"
            else:
                # 数据不足时用成交量简单评分
                vol_rank = min(100, int(coin["volume"] / 1e6))
                score = vol_rank
                signal = "📊数据不足"
                analysis = f"K线数据不足（{len(df) if df is not None else 0}根），暂按成交量参考。"
            results.append({
                "币种": coin["symbol"].replace("USDT", ""),
                "价格": round(coin["price"], 6),
                "24h涨跌": f"{coin['change']:+.2f}%",
                "24h量(百万U)": f"{coin['volume']/1e6:.1f}",
                "RSI": rsi,
                "AI信号": signal,
                "评分": score,
                "AI分析": analysis
            })
        return pd.DataFrame(results), len(cheap)
    except Exception as e:
        print(f"排名扫描错误: {e}")
        return pd.DataFrame(), 0
