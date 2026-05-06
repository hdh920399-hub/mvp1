class StrategyEngine:
    def __init__(self, params=None):
        self.params = params or {}
    def get_signal(self, df):
        return {"score": 0, "direction": "NEUTRAL"}
    def get_position_size(self, score, capital):
        return capital * 0.1
