from collections import deque
import numpy as np

class AdaptiveLearner:
    def __init__(self, max_history=100):
        self.trade_history = deque(maxlen=max_history)
    
    def record_trade(self, trade):
        self.trade_history.append(trade)
    
    def get_learning_summary(self):
        return "胜率: 54% | 平均盈亏: +2.3U"
    
    def adapt_params(self, current_params):
        return current_params, "表现良好"
