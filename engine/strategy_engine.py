import numpy as np
import pandas as pd

class StrategyEngine:
    def __init__(self, params=None):
        self.params = params or {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "rsi_weight": 0.3,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "macd_weight": 0.35,
            "ma_short": 20,
            "ma_long": 50,
            "ma_trend": 200,
            "ma_weight": 0.35,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.05,
            "max_position_pct": 0.3,
            "strong_signal_threshold": 25,
            "weak_signal_threshold": 10,
        }
    
    def get_signal(self, df):
        # 简化版，实际可扩展
        return {"score": 0, "direction": "NEUTRAL", "details": {}}
    
    def get_position_size(self, score, capital):
        max_pct = self.params["max_position_pct"]
        return capital * max_pct * 0.5