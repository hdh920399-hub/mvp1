import pandas as pd
import numpy as np

class RegimeDetector:
    def detect_regime(self, df):
        if df is None or len(df) < 100:
            return {"regime": "UNKNOWN", "adx": 0, "volatility": 0, "description": "数据不足", "recommended_action": "等待"}
        high, low, close = df["high"], df["low"], df["close"]
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (abs(minus_dm).rolling(14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-6)
        adx = dx.rolling(14).mean().iloc[-1]
        returns = close.pct_change().dropna()
        vol = returns.std() * np.sqrt(365) if len(returns) > 0 else 0
        # 调整阈值：ADX > 20 即视为趋势
        if adx > 20:
            regime = "TRENDING"
            desc = "趋势行情，适合趋势策略"
            action = "关注均线和MACD，可适当提高仓位"
        else:
            regime = "RANGING"
            desc = "震荡行情，适合高抛低吸"
            action = "关注RSI超买超卖，降低仓位"
        return {"regime": regime, "adx": round(adx,1), "volatility": round(vol,2), "description": desc, "recommended_action": action}
