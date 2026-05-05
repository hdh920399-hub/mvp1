import pandas as pd
import numpy as np

def calculate_directional_signal(df):
    """
    增强版多空信号：计算净得分（-100~100），并生成简评分析。
    """
    if df is None or len(df) < 50:
        return {
            "net_score": 0,
            "long_score": 0,
            "short_score": 0,
            "direction": "NEUTRAL",
            "summary": "数据不足",
            "analysis": "等待更多K线数据",
            "rsi": 50,
            "vol_ratio": 1.0
        }

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]
    reasons = []

    # ---------- RSI ----------
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    
    if rsi < 30:
        rsi_score = 30
        reasons.append(f"RSI={rsi:.1f}（超卖区），价格可能反弹，利好做多。")
    elif rsi < 45:
        rsi_score = 15
        reasons.append(f"RSI={rsi:.1f}（偏低），有上涨潜力，轻度利多。")
    elif rsi > 70:
        rsi_score = -30
        reasons.append(f"RSI={rsi:.1f}（超买区），回调风险增大，利好做空。")
    elif rsi > 55:
        rsi_score = -15
        reasons.append(f"RSI={rsi:.1f}（偏高），可能承压，轻度利空。")
    else:
        rsi_score = 0
        reasons.append(f"RSI={rsi:.1f}（中性区间）。")

    # ---------- MACD ----------
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    macd_val = macd_hist.iloc[-1]
    
    if macd_val > 0 and macd_hist.iloc[-2] <= 0:
        macd_score = 25
        reasons.append("MACD形成金叉，上涨动能增强，利多。")
    elif macd_val < 0 and macd_hist.iloc[-2] >= 0:
        macd_score = -25
        reasons.append("MACD形成死叉，下跌动能增强，利空。")
    elif macd_val > 0:
        macd_score = 10
        reasons.append("MACD柱为正，多头占据优势。")
    elif macd_val < 0:
        macd_score = -10
        reasons.append("MACD柱为负，空头占据优势。")
    else:
        macd_score = 0
        reasons.append("MACD无明显信号。")

    # ---------- 均线排列 ----------
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
    ma200 = close.rolling(200).mean().iloc[-1] if len(df) >= 200 else ma50
    price = close.iloc[-1]

    if price > ma20 > ma50 > ma200:
        ma_score = 25
        reasons.append("价格 > MA20 > MA50 > MA200，完全多头排列，趋势强劲。")
    elif price > ma20 > ma50:
        ma_score = 15
        reasons.append("价格 > MA20 > MA50，中期多头趋势。")
    elif price > ma20:
        ma_score = 8
        reasons.append("价格站上MA20，短期偏多。")
    elif price < ma20 < ma50 < ma200:
        ma_score = -25
        reasons.append("价格 < MA20 < MA50 < MA200，完全空头排列，趋势疲弱。")
    elif price < ma20 < ma50:
        ma_score = -15
        reasons.append("价格 < MA20 < MA50，中期空头趋势。")
    elif price < ma20:
        ma_score = -8
        reasons.append("价格跌破MA20，短期偏空。")
    else:
        ma_score = 0
        reasons.append("均线交织，趋势不明。")

    # ---------- 成交量 ----------
    avg_volume = volume.rolling(20).mean().iloc[-1]
    vol_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1
    if vol_ratio > 1.5:
        vol_score = 10
        reasons.append(f"成交量显著放大（{vol_ratio:.2f}倍），趋势可靠性增强。")
    elif vol_ratio > 1.2:
        vol_score = 5
        reasons.append(f"成交量温和放大（{vol_ratio:.2f}倍），有一定关注度。")
    else:
        vol_score = 0
        reasons.append("成交量正常或萎缩。")

    # 净得分
    net_score = rsi_score + macd_score + ma_score + vol_score
    net_score = max(-100, min(100, net_score))

    # 映射到0-100的多空分（仅用于展示）
    long_score = max(0, min(100, net_score + 50))
    short_score = 100 - long_score

    # 方向与总结
    if net_score >= 30:
        direction = "LONG"
        summary = f"🟢 强烈做多 (净得分: +{net_score})"
    elif net_score >= 10:
        direction = "LONG"
        summary = f"🟢 偏多 (净得分: +{net_score})"
    elif net_score <= -30:
        direction = "SHORT"
        summary = f"🔴 强烈做空 (净得分: {net_score})"
    elif net_score <= -10:
        direction = "SHORT"
        summary = f"🔴 偏空 (净得分: {net_score})"
    else:
        direction = "NEUTRAL"
        summary = f"⚪ 观望 (净得分: {net_score})"

    analysis_text = "；".join(reasons[:4]) + f"。综合净得分 = {int(net_score)}。"

    return {
        "net_score": int(net_score),
        "long_score": int(long_score),
        "short_score": int(short_score),
        "direction": direction,
        "summary": summary,
        "analysis": analysis_text,
        "rsi": round(rsi, 1),
        "vol_ratio": round(vol_ratio, 2)
    }
