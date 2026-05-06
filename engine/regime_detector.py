class RegimeDetector:
    def detect_regime(self, df):
        return {"regime": "NEUTRAL", "adx": 20, "volatility": 0.3, "recommended_action": "保持观察"}
