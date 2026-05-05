import plotly.graph_objects as go

def render(df, signal):

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"]
    ))

    if signal == "BUY":
        fig.add_annotation(
            x=df.index[-1],
            y=df["close"].iloc[-1],
            text="🟢 BUY",
            showarrow=True
        )

    if signal == "SELL":
        fig.add_annotation(
            x=df.index[-1],
            y=df["close"].iloc[-1],
            text="🔴 SELL",
            showarrow=True
        )

    fig.update_layout(
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=False
    )

    return fig
