import pandas as pd
import requests

def scan_cheap_coins_with_signal(max_price=1.0, limit=20, offset=0):
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        cheap = []
        for item in data:
            sym = item["symbol"]
            if not sym.endswith("USDT"):
                continue
            price = float(item["lastPrice"])
            vol = float(item["quoteVolume"])
            if price <= max_price and vol > 50000:
                cheap.append({"symbol": sym, "price": price, "change": float(item["priceChangePercent"]), "volume": vol})
        cheap.sort(key=lambda x: x["volume"], reverse=True)
        results = []
        for coin in cheap[offset:offset+limit]:
            results.append({
                "币种": coin["symbol"].replace("USDT",""),
                "价格": round(coin["price"],6),
                "24h涨跌": f"{coin['change']:+.2f}%",
                "24h量(百万U)": f"{coin['volume']/1e6:.1f}",
                "RSI": 50,
                "AI信号": "中性",
                "评分": 50
            })
        return pd.DataFrame(results), len(cheap)
    except:
        return pd.DataFrame(), 0