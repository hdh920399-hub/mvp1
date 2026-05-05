from datetime import datetime

class SimulatedTrader:
    def __init__(self, initial_balance=100):
        self.balance = initial_balance
        self.holdings = {}
        self.trades = []
        self.initial_balance = initial_balance
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.05
    
    def buy(self, symbol, price, usdt_amount, leverage=1):
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, "余额不足"
        quantity = usdt_amount / price
        self.holdings[symbol] = {"quantity": quantity, "avg_price": price, "side": "LONG"}
        self.balance -= margin
        self.trades.append({"action": "BUY", "symbol": symbol, "price": price, "quantity": quantity, "pnl": 0})
        return True, f"买入 {quantity:.4f}"
    
    def short(self, symbol, price, usdt_amount, leverage=1):
        margin = usdt_amount / leverage
        if margin > self.balance:
            return False, "余额不足"
        quantity = usdt_amount / price
        self.holdings[symbol] = {"quantity": quantity, "avg_price": price, "side": "SHORT"}
        self.balance -= margin
        self.trades.append({"action": "SHORT", "symbol": symbol, "price": price, "quantity": quantity, "pnl": 0})
        return True, f"做空 {quantity:.4f}"
    
    def update_positions(self, current_prices):
        closed = []
        # 简化版，不自动止盈止损，仅演示
        return closed
    
    def get_performance(self):
        return {
            "当前本金": self.balance,
            "总盈亏": self.balance - self.initial_balance,
            "收益率": (self.balance - self.initial_balance)/self.initial_balance*100,
            "交易次数": len(self.trades),
            "最大回撤": 0
        }