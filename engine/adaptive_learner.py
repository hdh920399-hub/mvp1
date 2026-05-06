import numpy as np
from collections import deque
from datetime import datetime

class AdaptiveLearner:
    def __init__(self, max_history=30):
        self.trade_history = deque(maxlen=max_history)  # 存储最近 max_history 笔平仓交易
        self.parameter_history = deque(maxlen=10)       # 记录参数调整历史

    def record_trade(self, trade):
        """记录一笔已平仓交易（应在每次平仓时调用）"""
        self.trade_history.append(trade)

    def get_recent_performance(self, lookback=20):
        """计算近期胜率和平均盈亏"""
        recent = list(self.trade_history)[-lookback:]
        if not recent:
            return {"win_rate": 0, "avg_pnl": 0, "sharpe": 0}
        pnls = [t["pnl"] for t in recent]
        wins = [p for p in pnls if p > 0]
        win_rate = len(wins) / len(recent) * 100
        avg_pnl = np.mean(pnls)
        sharpe = np.mean(pnls) / (np.std(pnls) + 1e-6)
        return {"win_rate": win_rate, "avg_pnl": avg_pnl, "sharpe": sharpe}

    def adapt_params(self, current_params):
        """根据近期交易表现调整参数"""
        perf = self.get_recent_performance(lookback=10)
        new_params = current_params.copy()
        reason = ""
        # 如果胜率低于40%，提高开仓最低评分，降低单笔风险
        if perf["win_rate"] < 40:
            new_params["min_score"] = min(80, current_params.get("min_score", 60) + 5)
            new_params["risk_pct"] = max(5, current_params.get("risk_pct", 10) - 1)
            reason = f"胜率{perf['win_rate']:.1f}%偏低，提高开仓评分至{new_params['min_score']}，降低风险至{new_params['risk_pct']}%"
        # 如果胜率高于70%，可适当降低评分门槛，略微提高风险
        elif perf["win_rate"] > 70:
            new_params["min_score"] = max(30, current_params.get("min_score", 60) - 5)
            new_params["risk_pct"] = min(20, current_params.get("risk_pct", 10) + 1)
            reason = f"胜率{perf['win_rate']:.1f}%较高，降低开仓评分至{new_params['min_score']}，提高风险至{new_params['risk_pct']}%"
        else:
            reason = f"胜率{perf['win_rate']:.1f}%正常，无需调整"
        self.parameter_history.append({
            "timestamp": datetime.now(),
            "reason": reason,
            "win_rate": perf["win_rate"]
        })
        return new_params, reason

    def get_learning_summary(self):
        perf = self.get_recent_performance()
        return f"近期胜率: {perf['win_rate']:.1f}% | 平均盈亏: {perf['avg_pnl']:.2f} U | 夏普: {perf['sharpe']:.2f}"
