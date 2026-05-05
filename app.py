import streamlit as st
from datetime import datetime
import pandas as pd

# 检查依赖
def check_dependencies():
    missing = []
    try:
        import streamlit
    except ImportError:
        missing.append("streamlit")
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import plotly
    except ImportError:
        missing.append("plotly")
    try:
        import requests
    except ImportError:
        missing.append("requests")
    try:
        import skopt
    except ImportError:
        missing.append("scikit-optimize")
    
    if missing:
        st.error(f"缺少必要的依赖包: {', '.join(missing)}")
        st.info("请运行以下命令安装依赖:")
        st.code("pip install -r requirements.txt")
        st.stop()

check_dependencies()

# 导入所有模块
from data.binance import get_klines, get_all_hot_symbols
from engine.ai_signals import calculate_directional_signal
from engine.strategy_engine import StrategyEngine
from engine.param_optimizer import GeneticOptimizer
from engine.param_optimizer_bayesian import BayesianOptimizer
from engine.adaptive_learner import AdaptiveLearner
from engine.regime_detector import RegimeDetector
from risk.portfolio import SimulatedTrader
from analysis.daily_summary import DailySummarizer
from analysis.backtest_exporter import BacktestExporter
from scanner.multi import scan_cheap_coins_with_signal
from ui.chart import create_pro_chart

# 缓存装饰器
@st.cache_data(ttl=300, show_spinner=False)
def get_klines_cached(symbol, interval, limit=150):
    return get_klines(symbol, interval, limit)

@st.cache_data(ttl=86400)
def get_hot_symbols_cached(limit=100):
    return get_all_hot_symbols(limit)

@st.cache_data(ttl=120)
def load_ranking_cached(max_price, limit):
    return scan_cheap_coins_with_signal(max_price=max_price, limit=limit, offset=0)

# 初始化 session state
if "trader" not in st.session_state:
    st.session_state.trader = SimulatedTrader(100)
if "strategy_engine" not in st.session_state:
    st.session_state.strategy_engine = StrategyEngine()
if "adaptive_learner" not in st.session_state:
    st.session_state.adaptive_learner = AdaptiveLearner()
if "regime_detector" not in st.session_state:
    st.session_state.regime_detector = RegimeDetector()
if "ranking_limit" not in st.session_state:
    st.session_state.ranking_limit = 20

st.set_page_config(page_title="AlphaPilot AI", layout="wide", page_icon="🤖")
st.title("🤖 AlphaPilot AI - 合约智能交易终端")
st.caption("币安U本位 | 多空双向 | 低价币扫描 | 遗传/贝叶斯优化 | 自适应学习 | 自动止盈止损 | 回测导出")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 配置")
    capital = st.number_input("💰 虚拟本金", 10, 1000, 100)
    max_price = st.slider("💰 最高价(USDT)", 0.1, 2.0, 1.0)
    if st.button("🔄 重置账户"):
        st.session_state.trader = SimulatedTrader(capital)
        st.cache_data.clear()
        st.rerun()
    if st.button("🗑️ 清空缓存"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 AI 自动交易")
    auto_trade_enabled = st.sidebar.checkbox("启用自动交易", value=False)

    if auto_trade_enabled:
        auto_interval = st.sidebar.selectbox("扫描间隔(秒)", [30, 60, 120], index=1)
        auto_max_positions = st.sidebar.number_input("最大同时持仓数", 1, 5, 3)
        auto_risk_per_trade = st.sidebar.slider("单笔风险(占总资金%)", 1, 20, 10) / 100
        auto_min_score = st.sidebar.slider("开仓最低评分", 40, 80, 55)

        if "last_auto_trade_time" not in st.session_state:
            st.session_state.last_auto_trade_time = datetime.now()

        now = datetime.now()
        time_diff = (now - st.session_state.last_auto_trade_time).total_seconds()

        if time_diff >= auto_interval:
            with st.spinner("AI 正在扫描市场并自动交易..."):
                from engine.auto_trader import auto_trade
                trade_result = auto_trade(
                    st.session_state.trader,
                    max_price=max_price,
                    max_positions=auto_max_positions,
                    risk_pct=auto_risk_per_trade,
                    min_score=auto_min_score
                )
                st.session_state.last_auto_trade_time = now
                if trade_result.get("trades"):
                    for trade in trade_result["trades"]:
                        st.toast(f"🤖 AI 自动{trade['action']} {trade['symbol']} {trade['price']:.6f}")
                else:
                    st.caption("当前无符合条件的自动交易信号")
            st.rerun()
        else:
            st.sidebar.caption(f"下次扫描: {auto_interval - int(time_diff)} 秒后")

    st.caption(f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 排行榜
st.subheader("🏆 低价潜力币排行榜")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📋 显示20个"): st.session_state.ranking_limit = 20; st.rerun()
with col2:
    if st.button("➕ 显示50个"): st.session_state.ranking_limit = 50; st.rerun()
with col3:
    if st.button("📄 显示全部"): st.session_state.ranking_limit = 200; st.rerun()

df_rank, total = load_ranking_cached(max_price, st.session_state.ranking_limit)
if not df_rank.empty:
    st.dataframe(df_rank, use_container_width=True, height=400)
    st.caption(f"共 {total} 个低价币")
else:
    st.warning("暂无数据")

st.markdown("---")

# 主分析区
col_left, col_right = st.columns([2,1])

with col_left:
    st.subheader("📈 专业K线分析")
    # 新代码：从排行榜获取币种（按 AI 评分排序）
# 先获取排行榜数据（已按评分排序）
ranking_df, _ = load_ranking_cached(max_price, 50)  # 取前50个评分最高的低价币
if not ranking_df.empty:
    # 构造币种完整名称（加上 USDT 后缀）
    ranked_symbols = [row["币种"] + "USDT" for _, row in ranking_df.iterrows()]
    # 可选：显示评分信息在下拉框中
    symbol_options = [f"{row['币种']} (评分:{row['评分']})" for _, row in ranking_df.iterrows()]
    selected_label = st.selectbox("选择AI推荐币种（按评分排序）", symbol_options, index=0)
    selected = selected_label.split(" (")[0] + "USDT"
else:
    # 如果没有低价币数据，回退到成交量排序的列表
    all_symbols = get_hot_symbols_cached(100)
    selected = st.selectbox("选择币种（成交量排序）", all_symbols, index=0)
    interval = st.selectbox("K线周期", ["1h","4h","1d"], index=1)
    df = get_klines_cached(selected, interval, limit=150)
    if df is not None and len(df) > 0:
        fig = create_pro_chart(df, selected)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("数据加载失败")

with col_right:
    st.subheader("🎯 AI实时信号")
    if df is not None and len(df) >= 50:
        signal = calculate_directional_signal(df)
        st.info(signal["summary"])
        st.metric("做多评分", signal["long_score"])
        st.metric("做空评分", signal["short_score"])
        st.caption(f"RSI: {signal['rsi']} | 量比: {signal['vol_ratio']}")
    st.markdown("---")
    st.subheader("💰 模拟交易")
    usdt = st.number_input("金额(USDT)", 5, 500, 20)
    lev = st.select_slider("杠杆", [1,2,3,5], value=1)
    col_b, col_s = st.columns(2)
    with col_b:
        if st.button("🟢 做多"):
            if df is not None:
                price = df["close"].iloc[-1]
                ok, msg = st.session_state.trader.buy(selected, price, usdt, lev)
                st.toast(msg)
    with col_s:
        if st.button("🔴 做空"):
            if df is not None:
                price = df["close"].iloc[-1]
                ok, msg = st.session_state.trader.short(selected, price, usdt, lev)
                st.toast(msg)

# 账户表现
st.markdown("---")
perf = st.session_state.trader.get_performance()
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("当前本金", f"{perf['当前本金']} U")
col_b.metric("总盈亏", f"{perf['总盈亏']:+.2f} U")
col_c.metric("收益率", f"{perf['收益率']}%")
col_d.metric("交易次数", perf["交易次数"])
if st.button("📥 导出回测报告"):
    trades_csv = BacktestExporter.export_trades_to_csv(st.session_state.trader.trades)
    perf_csv = BacktestExporter.export_performance_to_csv(perf)
    if trades_csv:
        st.download_button("下载交易记录", trades_csv, "trades.csv", "text/csv")
    st.download_button("下载账户表现", perf_csv, "performance.csv", "text/csv")

# 深度优化引擎（简化版）
st.markdown("---")
st.subheader("🧬 深度优化引擎")
tab1, tab2, tab3, tab4 = st.tabs(["市场状态", "策略参数", "优化器", "自适应学习"])
with tab1:
    regime = st.session_state.regime_detector.detect_regime(df)
    st.write(regime)
with tab2:
    st.json(st.session_state.strategy_engine.params)
with tab3:
    opt_type = st.radio("优化器", ["遗传算法", "贝叶斯优化"])
    if st.button("启动优化"):
        with st.spinner("优化中..."):
            if opt_type == "遗传算法":
                opt = GeneticOptimizer()
            else:
                opt = BayesianOptimizer()
            res = opt.optimize(df)
            st.success(res["message"])
            st.session_state.optimizer_result = res
    if 'optimizer_result' in st.session_state:
        st.json(st.session_state.optimizer_result.get("best_params", {}))
with tab4:
    st.write(st.session_state.adaptive_learner.get_learning_summary())
    if st.button("触发自适应调整"):
        new_params, reason = st.session_state.adaptive_learner.adapt_params(st.session_state.strategy_engine.params)
        st.info(reason)

# 每日总结
with st.expander("📋 每日总结报告"):
    if st.button("生成报告"):
        summarizer = DailySummarizer(st.session_state.trader)
        st.markdown(summarizer.generate())
