import json
import os
from datetime import datetime, timedelta
import numpy as np
from data.binance import get_current_funding_rate

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
                json.dump(state, f, default=self._json_serial, indent=2)
        except Exception as e:
            print(f"保存状态失败: {e}")

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
                for t in self.trades:
                    if "timestamp" in t and isinstance(t["timestamp"], str):
                        t["timestamp"] = datetime.fromisoformat(t["timestamp"])
                return True
        except Exception as e:
            print(f"加载状态失败: {e}")
            return False

    def _json_serial(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def _calc_funding_cost(self, pos, exit_time):
        """计算从开仓到平仓期间应支付/收取的资金费用（行业标准）"""
        if "last_funding_check" not in pos:
            # 第一次计算，使用开仓时间
            start = pos["open_time"]
        else:
            start = pos["last_funding_check"]
        # 币安资金费率每8小时结算一次，我们简化：按小时线性计算
        hours = (exit_time - start).total_seconds() / 3600
        if hours <= 0:
            return 0
        # 获取当前最新资金费率（假设整个期间费率不变，实际应多次查询，这里简化）
        fr_info = get_current_funding_rate(pos["symbol"])
        if fr_info is None:
            return 0
        funding_rate = fr_info["funding_rate"]
        notional = pos["notional"]
        # 多头支付（费率为正时支付），空头收取
        if pos["side"] == "LONG":
            cost = notional * funding_rate * hours
        else:
            cost = -notional * funding_rate * hours
        return cost

    def buy(self, symbol, price, usdt_amount, leverage=1, stop_loss_pct=None, take_profit_pct=None):
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, f"余额不足"
        quantity = usdt_amount / price
        sl_pct = stop_loss_pct if stop_loss_pct is not None else self.stop_loss_pct
        tp_pct = take_profit_pct if take_profit_pct is not None else self.take_profit_pct
        self.holdings[symbol] = {
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": price,
            "side": "LONG",
            "stop_loss": price * (1 - sl_pct),
            "take_profit": price * (1 + tp_pct),
            "leverage": leverage,
            "margin": margin,
            "notional": usdt_amount,
            "open_time": datetime.now(),
            "last_funding_check": datetime.now()
        }
        self.balance -= margin
        self.trades.append({
            "timestamp": datetime.now(),
            "symbol": symbol,
            "action": "BUY",
            "entry_price": price,
            "quantity": quantity,
            "margin": margin,
            "notional": usdt_amount,
            "leverage": leverage,
            "pnl": 0
        })
        self.save_state()
        return True, f"买入 {quantity:.4f}"

    def short(self, symbol, price, usdt_amount, leverage=1, stop_loss_pct=None, take_profit_pct=None):
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, f"余额不足"
        quantity = usdt_amount / price
        sl_pct = stop_loss_pct if stop_loss_pct is not None else self.stop_loss_pct
        tp_pct = take_profit_pct if take_profit_pct is not None else self.take_profit_pct
        self.holdings[symbol] = {
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": price,
            "side": "SHORT",
            "stop_loss": price * (1 + sl_pct),
            "take_profit": price * (1 - tp_pct),
            "leverage": leverage,
            "margin": margin,
            "notional": usdt_amount,
            "open_time": datetime.now(),
            "last_funding_check": datetime.now()
        }
        self.balance -= margin
        self.trades.append({
            "timestamp": datetime.now(),
            "symbol": symbol,
            "action": "SHORT",
            "entry_price": price,
            "quantity": quantity,
            "margin": margin,
            "notional": usdt_amount,
            "leverage": leverage,
            "pnl": 0
        })
        self.save_state()
        return True, f"做空 {quantity:.4f}"

    def _close_position(self, symbol, current_price, reason):
        pos = self.holdings[symbol]
        # 计算平仓盈亏
        if pos["side"] == "LONG":
            pnl = (current_price - pos["avg_price"]) * pos["quantity"]
        else:
            pnl = (pos["avg_price"] - current_price) * pos["quantity"]
        # 计算资金费率成本（行业标准）
        funding_cost = self._calc_funding_cost(pos, datetime.now())
        # 总盈亏 = 价格盈亏 - 资金费用（多头支付，空头收取）
        total_pnl = pnl - funding_cost if pos["side"] == "LONG" else pnl + funding_cost
        margin_used = pos["margin"]
        self.balance += margin_used + total_pnl
        self.trades.append({
            "timestamp": datetime.now(),
            "symbol": symbol,
            "action": "CLOSE",
            "entry_price": pos["avg_price"],
            "exit_price": current_price,
            "quantity": pos["quantity"],
            "margin": margin_used,
            "notional": pos["notional"],
            "leverage": pos["leverage"],
            "pnl": total_pnl,          # 已包含资金费率
            "funding_cost": funding_cost,
            "reason": reason
        })
        del self.holdings[symbol]
        self.save_state()
        return total_pnl

    def update_positions(self, current_prices):
        closed = []
        for symbol, pos in list(self.holdings.items()):
            price = current_prices.get(symbol)
            if price is None:
                continue
            if pos["side"] == "LONG":
                if price <= pos["stop_loss"]:
                    pnl = self._close_position(symbol, price, "stop_loss")
                    closed.append({"symbol": symbol, "reason": "stop_loss", "pnl": pnl})
                elif price >= pos["take_profit"]:
                    pnl = self._close_position(symbol, price, "take_profit")
                    closed.append({"symbol": symbol, "reason": "take_profit", "pnl": pnl})
            else:
                if price >= pos["stop_loss"]:
                    pnl = self._close_position(symbol, price, "stop_loss")
                    closed.append({"symbol": symbol, "reason": "stop_loss", "pnl": pnl})
                elif price <= pos["take_profit"]:
                    pnl = self._close_position(symbol, price, "take_profit")
                    closed.append({"symbol": symbol, "reason": "take_profit", "pnl": pnl})
        return closed

    def force_close_position(self, symbol, current_price):
        if symbol not in self.holdings:
            return False, 0, "无此持仓"
        pnl = self._close_position(symbol, current_price, "manual_close")
        return True, pnl, f"平仓成功，盈亏 {pnl:+.2f} U"

    def force_close_all_positions(self, current_prices):
        closed = []
        for sym in list(self.holdings.keys()):
            price = current_prices.get(sym)
            if price is None:
                continue
            success, pnl, msg = self.force_close_position(sym, price)
            if success:
                closed.append({"symbol": sym, "pnl": pnl})
        return closed

    def get_total_asset(self, current_prices=None):
        """总资产 = 可用余额 + 所有持仓的浮动盈亏总和（不含资金费率，因为未结算）"""
        if current_prices is None:
            current_prices = {}
        total_unrealized = 0.0
        for symbol, pos in self.holdings.items():
            price = current_prices.get(symbol, pos["avg_price"])
            if pos["side"] == "LONG":
                unrealized = (price - pos["avg_price"]) * pos["quantity"]
            else:
                unrealized = (pos["avg_price"] - price) * pos["quantity"]
            total_unrealized += unrealized
        return self.balance + total_unrealized

    def get_performance(self, current_prices=None):
        closed = [t for t in self.trades if t["action"] == "CLOSE"]
        realized_pnl = sum(t.get("pnl", 0) for t in closed)   # 已包含资金费率
        win_rate = len([t for t in closed if t.get("pnl", 0) > 0]) / max(1, len(closed)) * 100
        total_asset = self.get_total_asset(current_prices)
        return_percent = (realized_pnl / self.initial_balance) * 100
        return {
            "初始本金": self.initial_balance,
            "总资产": round(total_asset, 2),
            "可用余额": round(self.balance, 2),
            "已实现盈亏": round(realized_pnl, 2),
            "收益率": round(return_percent, 2),
            "平仓次数": len(closed),
            "胜率": round(win_rate, 1),
            "持仓数量": len(self.holdings)
        }
