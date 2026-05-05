from datetime import datetime
import numpy as np

class SimulatedTrader:
    """模拟交易引擎（带自动止盈止损）"""
    
    def __init__(self, initial_balance=100):
        self.balance = initial_balance
        self.holdings = {}      # 持仓 {symbol: {quantity, avg_price, side, stop_loss, take_profit}}
        self.trades = []        # 历史交易
        self.initial_balance = initial_balance
        
        # 风险参数
        self.stop_loss_pct = 0.02   # 默认止损 2%
        self.take_profit_pct = 0.05 # 默认止盈 5%
    
    def _register_trade(self, symbol, action, price, quantity, pnl, reason=""):
        """记录交易并反馈给自适应学习器"""
        trade_record = {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "action": action,
            "price": price,
            "quantity": quantity,
            "pnl": pnl,
            "reason": reason
        }
        self.trades.append(trade_record)
        # 尝试将交易记录传递给自适应学习器（如果存在）
        try:
            import streamlit as st
            if "adaptive_learner" in st.session_state:
                st.session_state.adaptive_learner.record_trade(trade_record)
        except:
            pass
        return trade_record
    
    def buy(self, symbol, price, usdt_amount, leverage=1):
        """买入开多"""
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, f"余额不足，可用 {self.balance:.2f} USDT"
        
        quantity = usdt_amount / price
        
        # 止盈止损价格
        stop_loss = price * (1 - self.stop_loss_pct)
        take_profit = price * (1 + self.take_profit_pct)
        
        self.holdings[symbol] = {
            "quantity": quantity,
            "avg_price": price,
            "side": "LONG",
            "entry_time": datetime.now(),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "leverage": leverage
        }
        self.balance -= margin
        
        self._register_trade(symbol, "BUY", price, quantity, 0)
        return True, f"✅ 买入 {quantity:.4f} {symbol} @ {price:.6f} (止损:{stop_loss:.4f})"
    
    def short(self, symbol, price, usdt_amount, leverage=1):
        """卖出开空"""
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, f"余额不足，可用 {self.balance:.2f} USDT"
        
        quantity = usdt_amount / price
        
        stop_loss = price * (1 + self.stop_loss_pct)
        take_profit = price * (1 - self.take_profit_pct)
        
        self.holdings[symbol] = {
            "quantity": quantity,
            "avg_price": price,
            "side": "SHORT",
            "entry_time": datetime.now(),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "leverage": leverage
        }
        self.balance -= margin
        
        self._register_trade(symbol, "SHORT", price, quantity, 0)
        return True, f"✅ 做空 {quantity:.4f} {symbol} @ {price:.6f} (止损:{stop_loss:.4f})"
    
    def update_positions(self, current_prices):
        """
        根据当前价格检查并自动平仓（止盈止损）
        返回 closed 列表
        """
        closed = []
        for symbol, pos in list(self.holdings.items()):
            price = current_prices.get(symbol)
            if price is None:
                continue
            
            should_close = False
            close_reason = ""
            pnl = 0
            qty = pos["quantity"]
            entry = pos["avg_price"]
            side = pos["side"]
            
            if side == "LONG":
                if price <= pos["stop_loss"]:
                    should_close = True
                    close_reason = "stop_loss"
                    pnl = (price - entry) * qty
                elif price >= pos["take_profit"]:
                    should_close = True
                    close_reason = "take_profit"
                    pnl = (price - entry) * qty
            else:  # SHORT
                if price >= pos["stop_loss"]:
                    should_close = True
                    close_reason = "stop_loss"
                    pnl = (entry - price) * qty
                elif price <= pos["take_profit"]:
                    should_close = True
                    close_reason = "take_profit"
                    pnl = (entry - price) * qty
            
            if should_close:
                # 释放保证金并结算盈亏
                margin_used = qty * entry / pos.get("leverage", 1)
                self.balance += margin_used + pnl
                self._register_trade(symbol, "CLOSE", price, qty, pnl, reason=close_reason)
                del self.holdings[symbol]
                closed.append({"symbol": symbol, "reason": close_reason, "pnl": pnl})
        
        return closed
    
    def get_performance(self):
        """获取账户表现（包含最大回撤）"""
        closed_trades = [t for t in self.trades if t["action"] == "CLOSE"]
        total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
        current_value = self.balance
        
        wins = [t for t in closed_trades if t.get("pnl", 0) > 0]
        win_rate = len(wins) / max(1, len(closed_trades)) * 100
        
        # 计算最大回撤
        if closed_trades:
            pnl_series = [t["pnl"] for t in closed_trades]
            cumsum = np.cumsum(pnl_series)
            peak = np.maximum.accumulate(cumsum)
            drawdown = np.max(peak - cumsum) if len(cumsum) > 0 else 0
        else:
            drawdown = 0
        
        return {
            "初始本金": self.initial_balance,
            "当前本金": round(current_value, 2),
            "总盈亏": round(current_value - self.initial_balance, 2),
            "收益率": round((current_value - self.initial_balance) / self.initial_balance * 100, 2),
            "交易次数": len(closed_trades),
            "胜率": round(win_rate, 1),
            "最大回撤": round(drawdown, 2)
        }
