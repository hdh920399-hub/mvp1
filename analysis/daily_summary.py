from datetime import datetime

class DailySummarizer:
    def __init__(self, trader):
        self.trader = trader
    
    def generate(self):
        perf = self.trader.get_performance()
        return f"📅 日报\n当前本金: {perf['当前本金']}U\n总盈亏: {perf['总盈亏']:.2f}U"
