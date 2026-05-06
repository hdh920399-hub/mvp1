import pandas as pd
class BacktestExporter:
    @staticmethod
    def export_trades_to_csv(trades):
        if not trades:
            return None
        return pd.DataFrame(trades).to_csv(index=False)
    @staticmethod
    def export_performance_to_csv(perf):
        return pd.DataFrame([perf]).to_csv(index=False)
