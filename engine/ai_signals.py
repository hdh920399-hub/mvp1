import pandas as pd
import numpy as np

def calculate_directional_signal(df):
    if df is None or len(df) < 50:
        return {"long_score": 0, "short_score": 0, "direction": "NEUTRAL", "summary": "数据不足", "rsi": 50, "vol_ratio": 1.0}
    
    close = df["close"]
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    
    if rsi < 30:
        rsi_long, rsi_short = 30, -20
    elif rsi < 45:
        rsi_long, rsi_short = 20, -10
    elif rsi < 55:
        rsi_long, rsi_short = 0, 0
    elif rsi < 70:
        rsi_long, rsi_short = -10, 20
    else:
        rsi_long, rsi_short = -20, 30
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - signal
    
    if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-2] <= 0:
        macd_long, macd_short = 25, -15
    elif macd_hist.iloc[-1] < 0 and macd_hist.iloc[-2] >= 0:
        macd_long, macd_short = -15, 25
    elif macd_hist.iloc[-1] > 0:
        macd_long, macd_short = 10, -5
    else:
        macd_long, macd_short = -5, 10
    
    # 均线
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    price = close.iloc[-1]
    
    if price > ma20 > ma50:
        ma_long, ma_short = 25, -10
    elif price < ma20 < ma50:
        ma_long, ma_short = -10, 25
    elif price > ma20:
        ma_long, ma_short = 10, -5
    elif price < ma20:
        ma_long, ma_short = -5, 10
    else:
        ma_long, ma_short = 0, 0
    
    # 成交量
    volume = df["volume"]
    avg_volume = volume.rolling(20).mean().iloc[-1]
    vol_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1
    if vol_ratio > 1.5:
        vol_boost = 10
    elif vol_ratio > 1.2:
        vol_boost = 5
    else:
        vol_boost = 0
    
    long_score = rsi_long + macd_long + ma_long + vol_boost
    short_score = rsi_short + macd_short + ma_short + vol_boost
    long_score = max(0, min(long_score, 100))
    short_score = max(0, min(short_score, 100))
    
    if long_score >= 50:
        direction, summary = "LONG", f"🟢 做多 (评分:{long_score})"
    elif short_score >= 50:
        direction, summary = "SHORT", f"🔴 做空 (评分:{short_score})"
    else:
        direction, summary = "NEUTRAL", f"⚪ 观望 (多:{long_score}/空:{short_score})"
    
    return {
        "long_score": long_score,
        "short_score": short_score,
        "direction": direction,
        "summary": summary,
        "rsi": round(rsi, 1),
        "vol_ratio": round(vol_ratio, 2)
    }
