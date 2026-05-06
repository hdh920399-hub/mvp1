import pandas as pd
import requests
from data.binance import get_klines

FUTURES_BASE_URL = "https://fapi.binance.com"

def scan_cheap_coins_with_signal(max_price=1.0, limit=20, offset=0):
    # 1. 获取 24h 行情数据
    try:
        resp = requests.get(
            f"{FUTURES_BASE_URL}/fapi/v1/ticker/24hr",
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        if resp.status_code != 200:
            raise Exception(f"API状态码异常: {resp.status_code}")
        data = resp.json()
    except Exception as e:
        raise Exception(f"无法获取币安24h行情数据: {e}")

    # 2. 筛选低价币（价格 ≤ max_price，成交量 > 50000 USDT）
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
        symbol = coin["symbol"]
        try:
            df = get_klines(symbol, "1h", limit=60)
            if df is None or len(df) < 30:
                print(f"跳过 {symbol}: K线数据不足")
                continue

            close = df["close"]
            high = df["high"]
            low = df["low"]

            # ---------- RSI ----------
            delta = close.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss
            rsi_val = (100 - (100 / (1 + rs))).iloc[-1]
            rsi = round(rsi_val, 1)

            # ---------- ATR ----------
            tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            price_now = coin["price"]

            # ---------- 基础评分与信号（多空导向名称）----------
            if rsi < 30:
                score = 80
                signal = "🟢 强烈做多"
                base = f"RSI={rsi}（超卖区），价格可能反弹，适合做多。"
            elif rsi < 45:
                score = 65
                signal = "🟢 做多"
                base = f"RSI={rsi}（偏低），有上涨潜力，可考虑做多。"
            elif rsi > 70:
                score = 20
                signal = "🔴 强烈做空"
                base = f"RSI={rsi}（超买区），回调风险增大，适合做空。"
            elif rsi > 55:
                score = 35
                signal = "🔴 做空"
                base = f"RSI={rsi}（偏高），可能面临压力，可考虑做空。"
            else:
                score = 50
                signal = "⚪ 观望"
                base = f"RSI={rsi}（中性区间），等待更明确信号。"

            # ---------- 均线描述 ----------
            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
            if price_now > ma20 and price_now > ma50:
                ma_desc = "价格位于MA20和MA50上方，短期趋势偏多。"
            elif price_now < ma20 and price_now < ma50:
                ma_desc = "价格位于MA20和MA50下方，短期趋势偏空。"
            else:
                ma_desc = "价格介于均线之间，趋势不明朗。"

            # ---------- 成交量分析 ----------
            avg_vol = df["volume"].rolling(20).mean().iloc[-1]
            vol_ratio = df["volume"].iloc[-1] / avg_vol if avg_vol != 0 else 1
            if vol_ratio > 1.5:
                vol_desc = f"成交量显著放大（{vol_ratio:.2f}倍），资金关注度高。"
            elif vol_ratio > 1.2:
                vol_desc = f"成交量温和放大（{vol_ratio:.2f}倍），有一定热度。"
            else:
                vol_desc = "成交量正常或萎缩，动能不足。"

            # ---------- 24h涨跌描述 ----------
            chg = coin["change"]
            if chg > 10:
                chg_desc = "24h涨幅较大，注意追高风险。"
            elif chg < -10:
                chg_desc = "24h跌幅较大，可能超跌反弹。"
            else:
                chg_desc = "24h波动温和。"

            # ---------- 动态杠杆计算（1-20倍）----------
            def calc_adx(df, period=14):
                high, low, close = df["high"], df["low"], df["close"]
                plus_dm = high.diff()
                minus_dm = low.diff()
                plus_dm[plus_dm < 0] = 0
                minus_dm[minus_dm > 0] = 0
                tr_val = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
                atr_val = tr_val.rolling(period).mean()
                plus_di = 100 * (plus_dm.rolling(period).mean() / atr_val)
                minus_di = 100 * (minus_dm.rolling(period).mean() / atr_val)
                dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.001)
                adx = dx.rolling(period).mean().iloc[-1]
                return adx if not pd.isna(adx) else 20

            adx = calc_adx(df, period=14)
            volatility_pct = atr / price_now * 100
            base_leverage = 20
            volatility_factor = max(0.2, min(1.0, 3.0 / (volatility_pct + 0.5)))
            adx_factor = min(1.5, max(0.5, adx / 40))
            score_factor = 0.8 + (score - 50) / 100
            rsi_penalty = 0.7 if (rsi > 80 or rsi < 20) else 1.0

            leverage = base_leverage * volatility_factor * adx_factor * score_factor * rsi_penalty
            leverage = max(1, min(20, round(leverage)))

            # ---------- 交易策略建议 ----------
            if score >= 70:
                direction = "做多"
                entry = price_now
                stop_loss = entry - 2 * atr
                take_profit = entry + 3 * atr
                risk_pct = (entry - stop_loss) / entry * 100
                position_pct = min(0.2, 0.02 / (risk_pct / 100)) if risk_pct > 0 else 0.1
                trade_advice = f"【交易策略】{direction} 入场 {entry:.4f}，止损 {stop_loss:.4f}，止盈 {take_profit:.4f}，建议仓位 {position_pct*100:.1f}%，杠杆 {leverage}x。"
            elif score <= 20:
                direction = "做空"
                entry = price_now
                stop_loss = entry + 2 * atr
                take_profit = entry - 3 * atr
                risk_pct = (stop_loss - entry) / entry * 100
                position_pct = min(0.2, 0.02 / (risk_pct / 100)) if risk_pct > 0 else 0.1
                trade_advice = f"【交易策略】{direction} 入场 {entry:.4f}，止损 {stop_loss:.4f}，止盈 {take_profit:.4f}，建议仓位 {position_pct*100:.1f}%，杠杆 {leverage}x。"
            else:
                trade_advice = "【交易策略】信号中性，建议观望。"

            analysis = f"{base} {ma_desc} {vol_desc} {chg_desc} 综合评分：{score}分。{trade_advice}"
            if rsi < 30 and vol_ratio > 1.2:
                analysis += " ⚡ 超卖+放量，短线反弹概率较高。"
            if rsi > 70 and vol_ratio > 1.5:
                analysis += " ⚠️ 超买+放量，注意回调风险。"

            results.append({
                "币种": symbol.replace("USDT", ""),
                "价格": round(price_now, 6),
                "24h涨跌": f"{chg:+.2f}%",
                "24h量(百万U)": f"{coin['volume']/1e6:.1f}",
                "RSI": rsi,
                "AI信号": signal,
                "评分": score,
                "建议杠杆": leverage,
                "AI分析": analysis
            })
        except Exception as e:
            print(f"处理 {symbol} 时出错: {e}")
            continue

    if not results:
        return pd.DataFrame(), 0

    results.sort(key=lambda x: x["评分"], reverse=True)
    return pd.DataFrame(results), len(cheap)
