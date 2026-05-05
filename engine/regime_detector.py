import numpy as np

class RegimeDetector:
    def detect_regime(self, df):
        return {"regime": "TRENDING", "adx": 38, "volatility": 0.42, "recommended_action": "关注均线"}
