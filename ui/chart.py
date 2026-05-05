import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_candlestick_chart(df, symbol):
    """创建专业K线图"""
    if df is None or df.empty:
        return go.Figure()
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3]
    )
    
    # K线图
    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="K线"
        ),
        row=1, col=1
    )
    
    # 移动平均线
    if len(df) >= 20:
        df["MA20"] = df["close"].rolling(20).mean()
        fig.add_trace(go.Scatter(x=df["time"], y=df["MA20"], mode="lines", name="MA20", line=dict(color="orange", width=1)), row=1, col=1)
    
    if len(df) >= 50:
        df["MA50"] = df["close"].rolling(50).mean()
        fig.add_trace(go.Scatter(x=df["time"], y=df["MA50"], mode="lines", name="MA50", line=dict(color="blue", width=1)), row=1, col=1)
    
    # 成交量
    colors = ["red" if df["close"].iloc[i] < df["open"].iloc[i] else "green" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df["time"], y=df["volume"], name="成交量", marker_color=colors), row=2, col=1)
    
    # 布局设置
    fig.update_layout(
        title=f"{symbol} K线图",
        xaxis_title="时间",
        yaxis_title="价格 (USDT)",
        template="plotly_dark",
        height=500,
        showlegend=True
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    
    return fig
