import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_pro_chart(df, symbol):
    if df is None or df.empty:
        return go.Figure()
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f"{symbol} K线图", "成交量", "RSI")
    )
    # 蜡烛图
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="K线"
    ), row=1, col=1)
    # 均线
    if len(df) >= 20:
        df["MA20"] = df["close"].rolling(20).mean()
        fig.add_trace(go.Scatter(x=df["time"], y=df["MA20"], mode="lines", name="MA20", line=dict(color="orange")), row=1, col=1)
    if len(df) >= 50:
        df["MA50"] = df["close"].rolling(50).mean()
        fig.add_trace(go.Scatter(x=df["time"], y=df["MA50"], mode="lines", name="MA50", line=dict(color="blue")), row=1, col=1)
    # 成交量
    colors = ["red" if df["close"].iloc[i] < df["open"].iloc[i] else "green" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df["time"], y=df["volume"], name="成交量", marker_color=colors), row=2, col=1)
    # RSI
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    fig.add_trace(go.Scatter(x=df["time"], y=rsi, mode="lines", name="RSI", line=dict(color="purple")), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
    fig.update_yaxes(title_text="价格 (USDT)", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    return fig
