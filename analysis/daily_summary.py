from datetime import datetime

class DailySummarizer:
    def __init__(self, trader, df=None):
        self.trader = trader
        self.df = df

    def generate(self):
        perf = self.trader.get_performance()
        today = datetime.now().strftime("%Y-%m-%d")
        return f"""
📅 **AI 智能交易日报 - {today}**
━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 初始本金: {perf['初始本金']} USDT
💰 当前本金: {perf['当前本金']} USDT
📈 总盈亏: {perf['总盈亏']:+.2f} USDT
📊 收益率: {perf['收益率']}%
🎯 交易次数: {perf['交易次数']}
🏆 胜率: {perf['胜率']}%
━━━━━━━━━━━━━━━━━━━━━━━━━━
*报告由 AlphaPilot AI 自动生成*
"""
