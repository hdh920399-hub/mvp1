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

@st.cache_data(ttl=15, show_spinner=False)
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
        st.error(f"获取排行榜失败: {e}")
        return pd.DataFrame(), 0

# ---------- session 初始化 ----------
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

# 默认值（保证刷新后仍保留）
st.session_state.setdefault("auto_interval", 60)
st.session_state.setdefault("max_positions", 3)
st.session_state.setdefault("risk_pct", 10)
st.session_state.setdefault("min_score", 60)
st.session_state.setdefault("capital", 100)
st.session_state.setdefault("max_price", 1.0)

st.title("🤖 AlphaPilot AI - 合约智能交易终端")
st.caption("币安U本位 | 多空双向 | 低价币扫描 | 遗传/贝叶斯优化 | 自适应学习 | 自动止盈止损 | AI自动交易 | 实时刷新")

# ---------- 侧边栏 ----------
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
                    st.toast(f"🤖 {trade['action']} {trade['symbol']} @ {trade['price']:.6f}")
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
                    st.toast(f"🤖 {trade['action']} {trade['symbol']} @ {trade['price']:.6f}")

    st.markdown("---")
    st.caption(f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ---------- 排行榜 ----------
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
    if "AI分析" in ranking_df.columns:
        ranking_df["AI分析"] = ranking_df["AI分析"].fillna("暂无详细分析")
    else:
        ranking_df["AI分析"] = "暂无详细分析"

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

    display_cols = ["币种", "价格", "24h涨跌", "24h量(百万U)", "RSI", "AI信号", "评分", "AI分析"]
    available_cols = [c for c in display_cols if c in ranking_df.columns]
    styled = ranking_df[available_cols].style.map(highlight_score, subset=['评分'])
    st.dataframe(styled, use_container_width=True, height=450)
    st.caption(f"💡 共 {total_count} 个低价币 | ≥70强烈推荐 | 55-69值得关注 | <40建议避开")
else:
    st.warning("暂无数据，请调高价格上限")

st.markdown("---")

# ---------- K线分析 ----------
st.subheader("📈 专业K线分析")
col_select, col_custom = st.columns([3, 1])
with col_select:
    if not ranking_df.empty:
        symbol_options = [f"{row['币种']} (评分:{row['评分']})" for _, row in ranking_df.iterrows()]
        if st.session_state.custom_symbol:
            custom_clean = st.session_state.custom_symbol.replace("USDT", "")
            default_idx = 0
            for i, opt in enumerate(symbol_options):
                if opt.startswith(custom_clean + " ("):
                    default_idx = i
                    break
        else:
            default_idx = 0
        selected_label = st.selectbox("选择AI推荐币种（按评分排序）", symbol_options, index=default_idx, key="rank_select")
        selected_symbol = selected_label.split(" (")[0] + "USDT"
    else:
        all_symbols = get_hot_symbols_cached(100)
        selected_symbol = st.selectbox("选择币种（成交量排序）", all_symbols, index=0, key="volume_select")
with col_custom:
    custom_input = st.text_input("或自定义币种 (例如 DOGEUSDT)", value="", key="custom_input").upper().strip()
    if custom_input:
        if not custom_input.endswith("USDT"):
            custom_input += "USDT"
        st.session_state.custom_symbol = custom_input
        selected_symbol = custom_input
        st.info(f"🔍 当前分析币种已切换至: **{selected_symbol}**")

interval = st.selectbox("K线周期", ["15m", "1h", "4h", "1d"], index=2, key="interval")
with st.spinner(f"📈 正在加载 {selected_symbol} K线数据..."):
    df = get_klines_cached(selected_symbol, interval, limit=150)

col_left, col_right = st.columns([2, 1])
with col_left:
    if df is not None and len(df) >= 20:
        fig = create_pro_chart(df, selected_symbol)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("K线数据加载中...")

with col_right:
    st.subheader("🎯 AI实时信号")
    if df is not None and len(df) >= 50:
        signal = calculate_directional_signal(df)
        st.info(signal["summary"])
        col_net, col_long, col_short = st.columns(3)
        with col_net:
            st.metric("净得分", signal["net_score"], delta="看多" if signal["net_score"] > 0 else "看空")
        with col_long:
            st.metric("做多评分", signal["long_score"])
        with col_short:
            st.metric("做空评分", signal["short_score"])
        st.caption(f"📊 RSI: {signal['rsi']} | 量比: {signal['vol_ratio']}")
        with st.expander("📝 评分理由分析", expanded=True):
            st.write(signal["analysis"])
    else:
        st.info("等待数据...")

# ---------- 账户表现 ----------
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
        st.download_button("📊 下载交易记录", trades_csv, "trades.csv", "text/csv")
    st.download_button("📈 下载账户表现", perf_csv, "performance.csv", "text/csv")

# ---------- 详细交易盈亏明细 ----------
with st.expander("📊 详细交易盈亏明细", expanded=False):
    if st.session_state.trader.holdings:
        st.subheader("📌 当前持仓 (未平仓)")
        current_prices = {}
        if df is not None:
            current_prices[selected_symbol] = df["close"].iloc[-1]
        holdings_data = []
        for sym, pos in st.session_state.trader.holdings.items():
            current_price = current_prices.get(sym, pos["avg_price"])
            if pos["side"] == "LONG":
                unrealized_pnl = (current_price - pos["avg_price"]) * pos["quantity"]
                unrealized_pnl_pct = (current_price / pos["avg_price"] - 1) * 100
            else:
                unrealized_pnl = (pos["avg_price"] - current_price) * pos["quantity"]
                unrealized_pnl_pct = (1 - current_price / pos["avg_price"]) * 100
            holdings_data.append({
                "币种": sym,
                "方向": pos["side"],
                "开仓价": round(pos["avg_price"], 6),
                "当前价": round(current_price, 6),
                "数量": pos["quantity"],
                "浮动盈亏(USDT)": round(unrealized_pnl, 2),
                "盈亏%": f"{unrealized_pnl_pct:+.2f}%",
                "止损价": round(pos["stop_loss"], 6),
                "止盈价": round(pos["take_profit"], 6),
                "杠杆": pos.get("leverage", 1)
            })
        st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)
    else:
        st.info("📭 当前无持仓")

    if st.session_state.trader.trades:
        closed_trades = [t for t in st.session_state.trader.trades if t.get("action") == "CLOSE"]
        if closed_trades:
            st.subheader("📜 历史平仓记录")
            df_trades = pd.DataFrame(closed_trades)
            show_cols = ["timestamp", "symbol", "action", "entry_price", "exit_price", "quantity", "pnl", "reason"]
            available = [c for c in show_cols if c in df_trades.columns]
            st.dataframe(df_trades[available], use_container_width=True)
        else:
            st.info("暂无平仓记录，等待止盈止损触发")
    else:
        st.info("暂无任何交易记录")

# ---------- 深度优化引擎 ----------
st.markdown("---")
with st.expander("🧬 深度优化引擎 (点击展开)", expanded=False):
    tab1, tab2, tab3, tab4 = st.tabs(["📊 市场状态", "⚙️ 策略参数", "🧬 优化器", "🧠 自适应学习"])
    with tab1:
        if df is not None and len(df) >= 100:
            regime = st.session_state.regime_detector.detect_regime(df)
            st.json(regime)
        else:
            st.warning("数据不足")
    with tab2:
        st.json(st.session_state.strategy_engine.params)
        if st.button("重置为默认参数"):
            st.session_state.strategy_engine = StrategyEngine()
            st.rerun()
    with tab3:
        opt_type = st.radio("优化器", ["遗传算法", "贝叶斯优化"], key="opt_type")
        if st.button("🚀 启动优化", key="run_optimizer"):
            if df is None or len(df) < 500:
                with st.spinner("数据量不足，正在获取更多K线数据..."):
                    more_df = get_klines_cached(selected_symbol, interval, limit=600)
                    if more_df is not None and len(more_df) >= 500:
                        opt_df = more_df
                        st.success(f"已获取 {len(more_df)} 根K线")
                    else:
                        st.error(f"数据不足（{len(more_df) if more_df is not None else 0}根），请选择更长周期（如1d）")
                        opt_df = None
            else:
                opt_df = df
            if opt_df is not None and len(opt_df) >= 500:
                with st.spinner("优化中..."):
                    if opt_type == "遗传算法":
                        opt = GeneticOptimizer()
                    else:
                        opt = BayesianOptimizer()
                    res = opt.optimize(opt_df)
                    st.session_state.optimizer_result = res
                    st.success(res.get("message", "优化完成"))
            else:
                st.warning("数据不足，请尝试更长K线周期")
        if st.session_state.optimizer_result:
            st.json(st.session_state.optimizer_result.get("best_params", {}))
    with tab4:
        st.markdown(st.session_state.adaptive_learner.get_learning_summary())
        if st.button("触发自适应调整", key="adapt_btn"):
            new_params, reason = st.session_state.adaptive_learner.adapt_params(st.session_state.strategy_engine.params)
            if new_params != st.session_state.strategy_engine.params:
                st.session_state.strategy_engine = StrategyEngine(new_params)
                st.success(f"已调整: {reason}")
            else:
                st.info(reason)

# ---------- 每日总结 ----------
with st.expander("📋 每日总结报告", expanded=False):
    if st.button("生成今日报告", key="gen_report"):
        summarizer = DailySummarizer(st.session_state.trader, df=df)
        st.markdown(summarizer.generate())

# ---------- 实时风控事件 ----------
with st.expander("🚨 实时风控事件", expanded=False):
    if st.button("刷新持仓检查", key="refresh_positions"):
        if df is not None:
            closed = st.session_state.trader.update_positions({selected_symbol: df["close"].iloc[-1]})
            if closed:
                for c in closed:
                    st.write(f"📢 {c['symbol']} {c['reason']} 平仓, 盈亏 {c['pnl']:+.2f} U")
            else:
                st.info("无平仓事件")

# ---------- 自动刷新 ----------
if st.session_state.get("auto_refresh", False):
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
