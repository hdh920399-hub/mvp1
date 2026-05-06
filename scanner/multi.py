import pandas as pd
import requests

def scan_cheap_coins_with_signal(max_price=1.0, limit=20, offset=0):
    # 模拟返回一些测试数据，保证排行榜有内容
    data = {
        "币种": ["HIVE", "RAVE", "DOGS", "SKYAI", "PENGU"],
        "价格": [0.068, 0.656, 0.000056, 0.788, 0.011],
        "24h涨跌": ["-15.58%", "-9.41%", "-21.40%", "+45.69%", "+4.36%"],
        "24h量(百万U)": [143.6, 125.2, 657.5, 549.1, 207.7],
        "RSI": [26.3, 21.0, 44.9, 54.6, 46.1],
        "AI信号": ["🟢超卖", "🟢超卖", "⚪中性", "🟢偏多", "⚪中性"],
        "评分": [80, 80, 50, 65, 50],
        "AI分析": [f"测试分析 {i}" for i in range(5)]
    }
    df = pd.DataFrame(data)
    return df, len(data["币种"])
