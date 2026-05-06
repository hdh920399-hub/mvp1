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
                    "volume": vol,
                    "high": float(item["highPrice"]),
                    "low": float(item["lowPrice"])
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

                # 获取最新价格与均线位置
                ma20 = close.rolling(20).mean().iloc[-1]
                ma50 = close.rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
                price_now = coin["price"]
                
                # 基础评分与信号
                if rsi < 30:
                    score = 80
                    signal = "🟢超卖"
                    base = f"RSI={rsi}（超卖区），价格可能反弹。"
                elif rsi < 45:
                    score = 65
                    signal = "🟢偏多"
                    base = f"RSI={rsi}（偏低），有上涨潜力。"
                elif rsi > 70:
                    score = 20
                    signal = "🔴超买"
                    base = f"RSI={rsi}（超买区），回调风险增大。"
                elif rsi > 55:
                    score = 35
                    signal = "🔴偏空"
                    base = f"RSI={rsi}（偏高），可能面临压力。"
                else:
                    score = 50
                    signal = "⚪中性"
                    base = f"RSI={rsi}（中性区间）。"

                # 均线位置补充
                if price_now > ma20 and price_now > ma50:
                    ma_desc = "价格位于MA20和MA50上方，短期趋势偏多。"
                elif price_now < ma20 and price_now < ma50:
                    ma_desc = "价格位于MA20和MA50下方，短期趋势偏空。"
                else:
                    ma_desc = "价格介于均线之间，趋势不明朗。"

                # 成交量分析
                vol_ratio = df["volume"].iloc[-1] / df["volume"].rolling(20).mean().iloc[-1] if df["volume"].rolling(20).mean().iloc[-1] != 0 else 1
                if vol_ratio > 1.5:
                    vol_desc = f"成交量显著放大（{vol_ratio:.2f}倍），资金关注度高。"
                elif vol_ratio > 1.2:
                    vol_desc = f"成交量温和放大（{vol_ratio:.2f}倍），有一定热度。"
                else:
                    vol_desc = "成交量正常或萎缩，动能不足。"

                # 24h涨跌幅评语
                chg = coin["change"]
                if chg > 10:
                    chg_desc = "24h涨幅较大，注意追高风险。"
                elif chg < -10:
                    chg_desc = "24h跌幅较大，可能超跌反弹。"
                else:
                    chg_desc = "24h波动温和。"

                # 综合分析
                analysis = f"{base} {ma_desc} {vol_desc} {chg_desc} 综合评分：{score}分。"
                
                # 对于超卖且成交量放大的币种，额外提示
                if rsi < 30 and vol_ratio > 1.2:
                    analysis += " ⚡ 超卖+放量，短线反弹概率较高。"
                if rsi > 70 and vol_ratio > 1.5:
                    analysis += " ⚠️ 超买+放量，注意回调风险。"

            else:
                # 数据不足时基于24h涨跌简单评分
                chg = coin["change"]
                if chg > 10:
                    signal = "📈大涨"
                    score = 60
                    analysis = f"K线数据不足（{len(df) if df is not None else 0}根），但24h涨幅{chg:.1f}%，短期强势。"
                elif chg < -10:
                    signal = "📉大跌"
                    score = 40
                    analysis = f"K线数据不足，24h跌幅{chg:.1f}%，可能超跌反弹。"
                else:
                    signal = "⚪数据不足"
                    score = 50
                    analysis = f"K线数据不足（{len(df) if df is not None else 0}根），暂按成交量排序。"

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
