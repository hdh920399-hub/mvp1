from datetime import datetime
import pandas as pd
import numpy as np

class DailySummarizer:
    def __init__(self, trader, df=None):
        self.trader = trader
        self.df = df

    def generate(self):
        perf = self.trader.get_performance()
        today = datetime.now().strftime("%Y-%m-%d")
        closed_trades = [t for t in self.trader.trades if t.get("action") == "CLOSE"]

        if not closed_trades:
            return f"📅 **AI 智能交易日报 - {today}**\n\n今日无平仓交易记录。\n当前本金: {perf['当前本金']} USDT\n总盈亏: {perf['总盈亏']:.2f} USDT"

        pnls = [t["pnl"] for t in closed_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        win_rate = len(wins) / len(closed_trades) * 100
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        max_win = max(wins) if wins else 0
        max_loss = min(losses) if losses else 0

        symbol_pnl = {}
        for t in closed_trades:
            sym = t["symbol"]
            symbol_pnl[sym] = symbol_pnl.get(sym, 0) + t["pnl"]
        best_symbol = max(symbol_pnl, key=symbol_pnl.get) if symbol_pnl else "无"
        worst_symbol = min(symbol_pnl, key=symbol_pnl.get) if symbol_pnl else "无"

        if win_rate > 55 and profit_factor > 1.5:
            advice = "策略表现优异，胜率和盈亏比均较高，可继续执行当前AI信号。"
        elif win_rate > 50:
            advice = "策略胜率尚可，但盈亏比偏低，建议优化止盈止损比例。"
        elif win_rate > 40:
            advice = "策略胜率一般，需结合市场状态调整参数，可尝试降低开仓评分阈值。"
        else:
            advice = "策略胜率偏低，建议暂停自动交易，回测优化参数或等待更明确信号。"

        market_advice = ""
        if self.df is not None and len(self.df) >= 100:
            try:
                from engine.regime_detector import RegimeDetector
                detector = RegimeDetector()
                regime = detector.detect_regime(self.df)
                market_advice = f"\n\n📈 **市场状态**: {regime['regime']} (ADX={regime['adx']:.1f})。{regime['recommended_action']}"
            except:
                pass

        report = f"""
📅 **AI 智能交易日报 - {today}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 **资金状况**
- 初始本金: {perf['初始本金']} USDT
- 当前本金: {perf['当前本金']} USDT
- 当日盈亏: {perf['总盈亏']:+.2f} USDT
- 收益率: {perf['收益率']}%

📊 **交易统计**
- 总交易次数: {len(closed_trades)}
- 盈利次数: {len(wins)} / 亏损次数: {len(losses)}
- 胜率: {win_rate:.1f}%
- 平均盈利: {avg_win:.2f} USDT
- 平均亏损: {avg_loss:.2f} USDT
- 盈亏比: {profit_factor:.2f}
- 最大单笔盈利: {max_win:.2f} USDT
- 最大单笔亏损: {max_loss:.2f} USDT

🏆 **币种表现**
- 最佳币种: {best_symbol} ({symbol_pnl.get(best_symbol, 0):+.2f} USDT)
- 最差币种: {worst_symbol} ({symbol_pnl.get(worst_symbol, 0):+.2f} USDT)

🤖 **AI 策略分析**
{advice}{market_advice}

💡 **明日建议**
- 若胜率 > 55%: 维持当前参数，积极交易
- 若胜率 40-55%: 降低单笔风险至 5%，提高开仓评分阈值
- 若胜率 < 40%: 暂停自动交易，等待市场明朗
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*报告由 AlphaPilot AI 自动生成*
"""
        return report
