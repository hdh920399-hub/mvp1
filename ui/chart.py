import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_pro_chart(df, symbol):
    # 极简版本确保图表显示
    if df is None or df.empty:
        return go.Figure()
    fig = go.Figure(data=[go.Scatter(x=df["time"] if "time" in df else list(range(len(df))), 
                                     y=df["close"] if "close" in df else [0]*len(df),
                                     mode='lines')])
    fig.update_layout(title=f"{symbol} K线图", template="plotly_dark")
    return fig
