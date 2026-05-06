from datetime import datetime
import numpy as np

class SimulatedTrader:
    def __init__(self, initial_balance=100):
        self.initial_balance = initial_balance
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.05
        self.balance = initial_balance
        self.holdings = {}
        self.trades = []

    def to_dict(self):
        """导出状态用于存储到 st.session_state"""
        return {
            "balance": self.balance,
            "holdings": self.holdings,
            "trades": self.trades,
            "initial_balance": self.initial_balance
        }

    @classmethod
    def from_dict(cls, data):
        """从字典恢复状态"""
        trader = cls(data["initial_balance"])
        trader.balance = data["balance"]
        trader.holdings = data["holdings"]
        trader.trades = data["trades"]
        # 确保 timestamp 是 datetime 对象
        for t in trader.trades:
            if "timestamp" in t and isinstance(t["timestamp"], str):
                t["timestamp"] = datetime.fromisoformat(t["timestamp"])
        return trader

    def buy(self, symbol, price, usdt_amount, leverage=1):
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, f"余额不足"
        quantity = usdt_amount / price
        self.holdings[symbol] = {
            "quantity": quantity,
            "avg_price": price,
            "side": "LONG",
            "stop_loss": price * (1 - self.stop_loss_pct),
            "take_profit": price * (1 + self.take_profit_pct),
            "leverage": leverage
        }
        self.balance -= margin
        self.trades.append({
            "timestamp": datetime.now(),
            "symbol": symbol,
            "action": "BUY",
            "entry_price": price,
            "quantity": quantity,
            "margin": margin,
            "pnl": 0
        })
        return True, f"买入 {quantity:.4f}"

    def short(self, symbol, price, usdt_amount, leverage=1):
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, f"余额不足"
        quantity = usdt_amount / price
        self.holdings[symbol] = {
            "quantity": quantity,
            "avg_price": price,
            "side": "SHORT",
            "stop_loss": price * (1 + self.stop_loss_pct),
            "take_profit": price * (1 - self.take_profit_pct),
            "leverage": leverage
        }
        self.balance -= margin
        self.trades.append({
            "timestamp": datetime.now(),
            "symbol": symbol,
            "action": "SHORT",
            "entry_price": price,
            "quantity": quantity,
            "margin": margin,
            "pnl": 0
        })
        return True, f"做空 {quantity:.4f}"

    def update_positions(self, current_prices):
        closed = []
        for symbol, pos in list(self.holdings.items()):
            price = current_prices.get(symbol)
            if price is None:
                continue
            pnl = 0
            reason = ""
            if pos["side"] == "LONG":
                if price <= pos["stop_loss"]:
                    pnl = (price - pos["avg_price"]) * pos["quantity"]
                    reason = "stop_loss"
                elif price >= pos["take_profit"]:
                    pnl = (price - pos["avg_price"]) * pos["quantity"]
                    reason = "take_profit"
            else:
                if price >= pos["stop_loss"]:
                    pnl = (pos["avg_price"] - price) * pos["quantity"]
                    reason = "stop_loss"
                elif price <= pos["take_profit"]:
                    pnl = (pos["avg_price"] - price) * pos["quantity"]
                    reason = "take_profit"
            if reason:
                margin_used = pos["quantity"] * pos["avg_price"] / pos.get("leverage", 1)
                self.balance += margin_used + pnl
                self.trades.append({
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "action": "CLOSE",
                    "entry_price": pos["avg_price"],
                    "exit_price": price,
                    "quantity": pos["quantity"],
                    "margin": margin_used,
                    "pnl": pnl,
                    "reason": reason
                })
                del self.holdings[symbol]
                closed.append({"symbol": symbol, "reason": reason, "pnl": pnl})
        return closed

    def get_total_asset(self, current_prices=None):
        if current_prices is None:
            current_prices = {}
        holdings_value = 0.0
        for symbol, pos in self.holdings.items():
            price = current_prices.get(symbol, pos["avg_price"])
            holdings_value += abs(pos["quantity"]) * price
        return self.balance + holdings_value

    def get_performance(self, current_prices=None):
        closed = [t for t in self.trades if t["action"] == "CLOSE"]
        realized_pnl = sum(t.get("pnl", 0) for t in closed)
        win_rate = len([t for t in closed if t.get("pnl", 0) > 0]) / max(1, len(closed)) * 100
        total_asset = self.get_total_asset(current_prices)
        return {
            "初始本金": self.initial_balance,
            "总资产": round(total_asset, 2),
            "可用余额": round(self.balance, 2),
            "已实现盈亏": round(realized_pnl, 2),
            "收益率": round((total_asset - self.initial_balance) / self.initial_balance * 100, 2),
            "平仓次数": len(closed),
            "胜率": round(win_rate, 1),
            "持仓数量": len(self.holdings)
        }
