import json
import os
from datetime import datetime

STATE_FILE = "trader_state.json"

class SimulatedTrader:
    def __init__(self, initial_balance=100):
        self.initial_balance = initial_balance
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.05
        if not self.load_state():
            self.balance = initial_balance
            self.holdings = {}
            self.trades = []

    def save_state(self):
        state = {
            "balance": self.balance,
            "holdings": self.holdings,
            "trades": self.trades,
            "initial_balance": self.initial_balance,
        }
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except:
            pass

    def load_state(self):
        if not os.path.exists(STATE_FILE):
            return False
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                self.balance = state["balance"]
                self.holdings = state["holdings"]
                self.trades = state["trades"]
                self.initial_balance = state.get("initial_balance", self.initial_balance)
                return True
        except:
            return False

    def buy(self, symbol, price, usdt_amount, leverage=1):
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, "余额不足"
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
            "pnl": 0
        })
        self.save_state()
        return True, f"买入 {quantity:.4f}"

    def short(self, symbol, price, usdt_amount, leverage=1):
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, "余额不足"
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
            "pnl": 0
        })
        self.save_state()
        return True, f"做空 {quantity:.4f}"

    def update_positions(self, current_prices):
        closed = []
        for symbol, pos in list(self.holdings.items()):
            price = current_prices.get(symbol)
            if not price:
                continue
            if pos["side"] == "LONG":
                if price <= pos["stop_loss"] or price >= pos["take_profit"]:
                    pnl = (price - pos["avg_price"]) * pos["quantity"]
                    reason = "stop_loss" if price <= pos["stop_loss"] else "take_profit"
                    # 平仓逻辑
                    margin_used = pos["quantity"] * pos["avg_price"] / pos.get("leverage", 1)
                    self.balance += margin_used + pnl
                    self.trades.append({
                        "timestamp": datetime.now(),
                        "symbol": symbol,
                        "action": "CLOSE",
                        "entry_price": pos["avg_price"],
                        "exit_price": price,
                        "quantity": pos["quantity"],
                        "pnl": pnl,
                        "reason": reason
                    })
                    del self.holdings[symbol]
                    closed.append({"symbol": symbol, "reason": reason, "pnl": pnl})
            else:  # SHORT
                if price >= pos["stop_loss"] or price <= pos["take_profit"]:
                    pnl = (pos["avg_price"] - price) * pos["quantity"]
                    reason = "stop_loss" if price >= pos["stop_loss"] else "take_profit"
                    margin_used = pos["quantity"] * pos["avg_price"] / pos.get("leverage", 1)
                    self.balance += margin_used + pnl
                    self.trades.append({
                        "timestamp": datetime.now(),
                        "symbol": symbol,
                        "action": "CLOSE",
                        "entry_price": pos["avg_price"],
                        "exit_price": price,
                        "quantity": pos["quantity"],
                        "pnl": pnl,
                        "reason": reason
                    })
                    del self.holdings[symbol]
                    closed.append({"symbol": symbol, "reason": reason, "pnl": pnl})
        if closed:
            self.save_state()
        return closed

    def get_performance(self):
        closed = [t for t in self.trades if t["action"] == "CLOSE"]
        total_pnl = sum(t.get("pnl", 0) for t in closed)
        win_rate = len([t for t in closed if t.get("pnl", 0) > 0]) / max(1, len(closed)) * 100
        return {
            "初始本金": self.initial_balance,
            "当前本金": round(self.balance, 2),
            "总盈亏": round(self.balance - self.initial_balance, 2),
            "收益率": round((self.balance - self.initial_balance) / self.initial_balance * 100, 2),
            "交易次数": len(closed),
            "胜率": round(win_rate, 1),
            "最大回撤": 0
        }
