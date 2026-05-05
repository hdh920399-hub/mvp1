import pandas as pd
import numpy as np

def calculate_signals(df):
    """计算RSI、MACD、均线信号"""
    if df is None or len(df) < 50:
        return {"rsi": "数据不足", "macd": "数据不足", "ma": "数据不足"}
    
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
        rsi_signal = "超卖 🟢 买入"
    elif rsi > 70:
        rsi_signal = "超卖 🔴 卖出"
    else:
        rsi_signal = "中性 ⚪ 观望"
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    
    if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        macd_signal = "金叉 🟢 买入"
    elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        macd_signal = "死叉 🔴 卖出"
    else:
        macd_signal = "无信号 ⚪ 观望"
    
    # 均线
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1] if len(df) >= 200 else ma50
    
    if ma20 > ma50 > ma200:
        ma_signal = "多头排列 🟢 买入"
    elif ma20 < ma50 < ma200:
        ma_signal = "空头排列 🔴 卖出"
    else:
        ma_signal = "震荡 ⚪ 观望"
    
    return {
        "rsi": f"RSI: {rsi:.1f} | {rsi_signal}",
        "macd": macd_signal,
        "ma": ma_signal
    }
