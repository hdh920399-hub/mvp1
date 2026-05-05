import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_pro_chart(df, symbol):
    if df is None or df.empty:
        return go.Figure()
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Candlestick(x=df["time"], open=df["open"], high=df["high"], low=df["low"], close=df["close"]))
    fig.update_layout(template="plotly_dark", height=500)
    return fig
