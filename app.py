import streamlit as st
from datetime import datetime
import pandas as pd
import time

from data.binance import get_klines, get_all_hot_symbols
from engine.ai_signals import calculate_directional_signal
from engine.strategy_engine import StrategyEngine
from engine.param_optimizer import GeneticOptimizer
from engine.param_optimizer_bayesian import BayesianOptimizer
from engine.adaptive_learner import AdaptiveLearner
from engine.regime_detector import RegimeDetector
from engine.auto_trader import auto_trade
from risk.portfolio import SimulatedTrader
from analysis.daily_summary import DailySummarizer
from analysis.backtest_exporter import BacktestExporter
from scanner.multi import scan_cheap_coins_with_signal
from ui.chart import create_pro_chart

st.set_page_config(page_title="AlphaPilot AI", layout="wide", page_icon="🤖")

# 缓存函数
@st.cache_data(ttl=60, show_spinner=False)
def get_klines_cached(symbol, interval, limit=150):
    return get_klines(symbol, interval, limit)

@st.cache_data(ttl=86400, show_spinner=False)
def get_hot_symbols_cached(limit=100):
    return get_all_hot_symbols(limit)

@st.cache_data(ttl=60, show_spinner=False)
def load_ranking_cached(max_price, limit):
    try:
        df, total = scan_cheap_coins_with_signal(max_price=max_price, limit=limit, offset=0)
        return df, total
    except Exception as e:
        st.error(f"❌ 获取排行榜失败: {e}")
        return pd.DataFrame(), 0

# 初始化 session
if "trader" not in st.session_state:
    st.session_state.trader = SimulatedTrader(100)
if "strategy_engine" not in st.session_state:
    st.session_state.strategy_engine = StrategyEngine()
if "adaptive_learner" not in st.session_state:
    st.session_state.adaptive_learner = AdaptiveLearner()
if "regime_detector" not in st.session_state:
    st.session_state.regime_detector = RegimeDetector()
if "optimizer_result" not in st.session_state:
    st.session_state.optimizer_result = None
if "ranking_limit" not in st.session_state:
    st.session_state.ranking_limit = 20
if "auto_trade_last_time" not in st.session_state:
    st.session_state.auto_trade_last_time = datetime.now()
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "custom_symbol" not in st.session_state:
    st.session_state.custom_symbol = ""

st.session_state.setdefault("auto_interval", 60)
st.session_state.setdefault("max_positions", 3)
st.session_state.setdefault("risk_pct", 10)
st.session_state.setdefault("min_score", 60)
st.session_state.setdefault("capital", 100)
st.session_state.setdefault("max_price", 1.0)

st.title("🤖 AlphaPilot AI - 合约智能交易终端")
st.caption("币安U本位 | 多空双向 | 低价币扫描 | 遗传/贝叶斯优化 | 自适应学习 | 自动止盈止损 | AI自动交易 | 实时刷新")

# 侧边栏（略，保持原有）
with st.sidebar:
    st.header("⚙️ 配置")
    capital = st.number_input("💰 虚拟本金", min_value=10, value=st.session_state.capital, step=10, key="capital")
    max_price = st.slider("💰 最高价(USDT)", 0.1, 100.0, st.session_state.max_price, step=0.5, key="max_price")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重置账户"):
            st.session_state.trader = SimulatedTrader(capital)
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("🗑️ 清空缓存"):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    st.subheader("🔄 数据刷新")
    auto_refresh = st.checkbox("🌊 启用实时刷新 (每30秒)", value=st.session_state.auto_refresh, key="auto_refresh")
    if st.button("🔄 手动刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("🤖 AI 自动交易")
    auto_interval = st.selectbox("扫描间隔(秒)", [30, 60, 120], index=[30,60,120].index(st.session_state.auto_interval), key="auto_interval")
    max_positions = st.number_input("最大同时持仓数", 1, 5, st.session_state.max_positions, key="max_positions")
    risk_pct = st.slider("单笔风险(占总资金%)", 1, 20, st.session_state.risk_pct, key="risk_pct") / 100
    min_score = st.slider("开仓最低评分", 5, 80, st.session_state.min_score, key="min_score")

    if st.button("⚡ 立即扫描交易", use_container_width=True):
        with st.spinner("正在扫描市场并执行交易..."):
            result = auto_trade(
                st.session_state.trader,
                max_price=1.0,
                max_positions=max_positions,
                risk_pct=risk_pct,
                min_score=min_score
            )
            if result.get("trades"):
                for trade in result["trades"]:
                    st.toast(f"🤖 {trade['action']} {trade['symbol']} @ {trade['price']:.6f} (杠杆:{trade['leverage']}x)")
            st.rerun()

    now = datetime.now()
    diff = (now - st.session_state.auto_trade_last_time).total_seconds()
    remaining = max(0, int(auto_interval - diff))
    st.caption(f"⏳ 下次扫描: {remaining} 秒后")
    if remaining <= 0:
        with st.spinner("AI 正在扫描市场并执行交易..."):
            result = auto_trade(
                st.session_state.trader,
                max_price=1.0,
                max_positions=max_positions,
                risk_pct=risk_pct,
                min_score=min_score
            )
            st.session_state.auto_trade_last_time = now
            if result.get("trades"):
                for trade in result["trades"]:
                    st.toast(f"🤖 {trade['action']} {trade['symbol']} @ {trade['price']:.6f} (杠杆:{trade['leverage']}x)")

    st.markdown("---")
    st.caption(f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 排行榜（包含建议杠杆列）
st.subheader("🏆 低价潜力币排行榜")
col_btn1, col_btn2, col_btn3, col_refresh = st.columns(4)
with col_btn1:
    if st.button("📋 显示20个"):
        st.session_state.ranking_limit = 20
        st.rerun()
with col_btn2:
    if st.button("➕ 显示50个"):
        st.session_state.ranking_limit = 50
        st.rerun()
with col_btn3:
    if st.button("📄 显示全部"):
        st.session_state.ranking_limit = 200
        st.rerun()
with col_refresh:
    if st.button("🔄 强制刷新排行", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

ranking_df, total_count = load_ranking_cached(max_price, st.session_state.ranking_limit)

if not ranking_df.empty:
    def highlight_score(val):
        if isinstance(val, (int, float)):
            if val >= 70:
                return 'background-color: #2e7d32; color: white'
            if val >= 55:
                return 'background-color: #1565c0; color: white'
            if val >= 40:
                return 'background-color: #f57c00; color: white'
            return 'background-color: #c62828; color: white'
        return ''

    # 确保存在建议杠杆列
    if "建议杠杆" not in ranking_df.columns:
        ranking_df["建议杠杆"] = 1
    display_cols = ["币种", "价格", "24h涨跌", "24h量(百万U)", "RSI", "AI信号", "评分", "建议杠杆", "AI分析"]
    available_cols = [c for c in display_cols if c in ranking_df.columns]
    styled = ranking_df[available_cols].style.map(highlight_score, subset=['评分'])
    st.dataframe(styled, use_container_width=True, height=500)
    st.caption(f"💡 共 {total_count} 个低价币 | ≥70强烈推荐 | 55-69值得关注 | <40建议避开")
else:
    st.warning("暂无数据，请调高价格上限或检查币安 API 连接")

st.markdown("---")

# 专业K线分析（略，保持原有，注意传入selected_symbol）
# ... 省略（与之前相同）...
# 为了节省篇幅，这里假设你已经有了之前的完整K线分析代码，只需确保 selected_symbol 被正确定义。
# 实际部署时请使用之前完整的 app.py 中的该部分代码。

# 账户表现（使用修复后的 performance）
# 需要获取当前价格字典
current_prices = {}
if df is not None:
    current_prices[selected_symbol] = df["close"].iloc[-1]
perf = st.session_state.trader.get_performance(current_prices)

col_a, col_b, col_c, col_d, col_e = st.columns(5)
col_a.metric("总资产", f"{perf['总资产']} U", delta=f"{perf['收益率']:+.1f}%")
col_b.metric("可用余额", f"{perf['可用余额']} U")
col_c.metric("已实现盈亏", f"{perf['已实现盈亏']:+.2f} U")
col_d.metric("平仓次数", perf['平仓次数'])
col_e.metric("当前持仓数", perf['持仓数量'])

if st.button("📥 导出回测报告"):
    trades_csv = BacktestExporter.export_trades_to_csv(st.session_state.trader.trades)
    perf_csv = BacktestExporter.export_performance_to_csv(perf)
    if trades_csv:
        st.download_button("📊 交易记录", trades_csv, "trades.csv")
    st.download_button("📈 账户表现", perf_csv, "performance.csv")

# 详细交易明细（略，保持原有）
# ...

# 深度优化引擎（略，保持原有）
# ...

# 每日总结（传入df）
with st.expander("📋 每日总结报告", expanded=False):
    if st.button("生成今日报告", key="gen_report"):
        summarizer = DailySummarizer(st.session_state.trader, df=df)
        st.markdown(summarizer.generate())

# 实时风控事件（略）
# ...

# 自动刷新逻辑
if st.session_state.get("auto_refresh", False):
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
