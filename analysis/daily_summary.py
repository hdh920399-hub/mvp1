from datetime import datetime
class DailySummarizer:
    def __init__(self, trader):
        self.trader = trader
    def generate(self):
        perf = self.trader.get_performance()
        return f"📅 日报\n初始本金: {perf['初始本金']}U\n当前: {perf['当前本金']}U\n盈亏: {perf['总盈亏']:.2f}U"
