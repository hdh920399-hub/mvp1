import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import time

from data.binance import get_klines, get_all_hot_symbols, get_funding_rate as get_current_funding_rate
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

# 时区：北京时间 = UTC+8
def now_cn():
    return datetime.utcnow() + timedelta(hours=8)

st.set_page_config(page_title="AlphaPilot AI", layout="wide", page_icon="🤖")

# ---------- 保存交易器状态 ----------
def save_trader_state():
    if "trader" in st.session_state:
        st.session_state.trader_data = {
            "balance": st.session_state.trader.balance,
            "holdings": st.session_state.trader.holdings,
            "trades": st.session_state.trader.trades,
            "initial_balance": st.session_state.trader.initial_balance
        }

# ---------- 缓存函数 ----------
@st.cache_data(ttl=15, show_spinner=False)
def get_klines_cached(symbol, interval, limit=150):
    return get_klines(symbol, interval, limit)

@st.cache_data(ttl=86400, show_spinner=False)
def get_hot_symbols_cached(limit=100):
    return get_all_hot_symbols(limit)

@st.cache_data(ttl=20, show_spinner=False)
def load_ranking_cached(max_price, limit):
    try:
        df, total = scan_cheap_coins_with_signal(max_price=max_price, limit=limit, offset=0)
        return df, total
    except Exception as e:
        st.error(f"❌ 获取排行榜失败: {e}")
        return pd.DataFrame(), 0

# ---------- 初始化 Session State ----------
if "trader" not in st.session_state:
    st.session_state.trader = SimulatedTrader(100)
    save_trader_state()
else:
    if not st.session_state.trader.holdings and not st.session_state.trader.trades:
        backup = st.session_state.get("trader_data", None)
        if backup:
            st.session_state.trader.balance = backup["balance"]
            st.session_state.trader.holdings = backup["holdings"]
            st.session_state.trader.trades = backup["trades"]
            for t in st.session_state.trader.trades:
                if "timestamp" in t and isinstance(t["timestamp"], str):
                    t["timestamp"] = datetime.fromisoformat(t["timestamp"])

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
    st.session_state.auto_trade_last_time = now_cn()
if "custom_symbol" not in st.session_state:
    st.session_state.custom_symbol = ""

# 配置项默认值（刷新后保存）
st.session_state.setdefault("auto_interval", 60)
st.session_state.setdefault("max_positions", 5)          # 默认最大持仓数改为5
st.session_state.setdefault("risk_pct", 10)
st.session_state.setdefault("min_score", 20)
st.session_state.setdefault("capital", 100)
st.session_state.setdefault("max_price", 5.0)            # 最高价默认改为5（10以下）
st.session_state.setdefault("stop_loss_pct", 2.0)
st.session_state.setdefault("take_profit_pct", 5.0)
st.session_state.setdefault("auto_refresh", True)        # 默认启用实时刷新

st.title("🤖 AlphaPilot AI - 合约智能交易终端")
st.caption("币安U本位 | 多空双向 | 低价币扫描 | 遗传/贝叶斯优化 | 自适应学习 | 自动止盈止损 | AI自动交易 | 实时刷新")

# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("⚙️ 配置")
    capital = st.number_input("💰 虚拟本金", min_value=10, value=st.session_state.capital, step=10, key="capital")
    max_price = st.slider("💰 最高价(USDT)", 0.1, 100.0, value=st.session_state.max_price, step=0.5, key="max_price")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重置账户"):
            st.session_state.trader = SimulatedTrader(capital)
            save_trader_state()
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
    st.subheader("🎯 风控参数")
    stop_loss_pct = st.number_input("止损百分比 (%)", min_value=0.1, max_value=10.0, value=st.session_state.stop_loss_pct, step=0.1, key="stop_loss_pct") / 100
    take_profit_pct = st.number_input("止盈百分比 (%)", min_value=0.1, max_value=20.0, value=st.session_state.take_profit_pct, step=0.1, key="take_profit_pct") / 100

    st.markdown("---")
    st.subheader("🤖 AI 自动交易")
    auto_interval = st.selectbox("扫描间隔(秒)", [30, 60, 120], index=[30,60,120].index(st.session_state.auto_interval), key="auto_interval")
    max_positions = st.number_input("最大同时持仓数", 1, 5, value=st.session_state.max_positions, key="max_positions")
    risk_pct = st.slider("单笔风险(占总资金%)", 1, 20, value=st.session_state.risk_pct, key="risk_pct") / 100
    min_score = st.slider("开仓最低评分", 0, 100, value=st.session_state.min_score, key="min_score")

    if st.button("⚡ 立即扫描交易", use_container_width=True):
        with st.spinner("正在扫描市场并执行交易..."):
            result = auto_trade(
                st.session_state.trader,
                max_price=1.0,
                max_positions=max_positions,
                risk_pct=risk_pct,
                min_score=min_score,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct
            )
            if result.get("trades"):
                save_trader_state()
                for trade in result["trades"]:
                    st.toast(f"🤖 {trade['action']} {trade['symbol']} @ {trade['price']:.6f} (杠杆:{trade['leverage']}x)")
            st.rerun()

    now = now_cn()
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
                min_score=min_score,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct
            )
            st.session_state.auto_trade_last_time = now
            if result.get("trades"):
                save_trader_state()
                for trade in result["trades"]:
                    st.toast(f"🤖 {trade['action']} {trade['symbol']} @ {trade['price']:.6f} (杠杆:{trade['leverage']}x)")

    # 强制平仓所有持仓按钮
    if st.button("🔒 强制平仓所有持仓", use_container_width=True):
        if st.session_state.trader.holdings:
            closing_prices = {}
            for sym in st.session_state.trader.holdings.keys():
                price = None
                if 'ranking_df' in locals() and not ranking_df.empty:
                    row = ranking_df[ranking_df["币种"] + "USDT" == sym]
                    if not row.empty:
                        price = row.iloc[0]["价格"]
                if price is None:
                    last_k = get_klines_cached(sym, "1h", limit=1)
                    if last_k is not None and len(last_k) > 0:
                        price = last_k["close"].iloc[-1]
                if price:
                    closing_prices[sym] = price
            if closing_prices:
                closed = st.session_state.trader.force_close_all_positions(closing_prices)
                if closed:
                    for c in closed:
                        st.session_state.adaptive_learner.record_trade({
                            "symbol": c["symbol"],
                            "pnl": c["pnl"],
                            "timestamp": now_cn()
                        })
                    save_trader_state()
                    st.toast(f"已强制平仓 {len(closed)} 个仓位")
                    st.rerun()
                else:
                    st.toast("无平仓发生")
            else:
                st.toast("无法获取当前价格，平仓失败")
        else:
            st.toast("当前无持仓")

    st.markdown("---")
    st.caption(f"⏱️ {now_cn().strftime('%Y-%m-%d %H:%M:%S')}")

# ---------- 低价潜力币排行榜 ----------
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

    if "AI分析" not in ranking_df.columns:
        ranking_df["AI分析"] = "暂无详细分析"
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

# ---------- 专业K线分析 ----------
st.subheader("📈 专业K线分析")
df = None
selected_symbol = "BTCUSDT"

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
        try:
            fig = create_pro_chart(df, selected_symbol)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"图表渲染失败: {e}")
    else:
        st.warning("K线数据不足（少于20根）")

with col_right:
    st.subheader("🎯 AI实时信号")
    if df is not None and len(df) >= 50:
        signal = calculate_directional_signal(df)
        st.info(signal["summary"])
        col_net, col_long, col_short = st.columns(3)
        with col_net:
            st.metric("净得分", signal["net_score"])
        with col_long:
            st.metric("做多评分", signal["long_score"])
        with col_short:
            st.metric("做空评分", signal["short_score"])
        st.caption(f"📊 RSI: {signal['rsi']} | 量比: {signal['vol_ratio']}")
        with st.expander("📝 评分理由分析", expanded=True):
            st.write(signal["analysis"])
    else:
        st.info("等待K线数据（至少50根）...")

# ---------- 构建实时价格字典 ----------
if "current_prices" in st.session_state and st.session_state.current_prices:
    current_prices = st.session_state.current_prices
else:
    current_prices = {}
    if df is not None and len(df) > 0:
        current_prices[selected_symbol] = df["close"].iloc[-1]
    if not ranking_df.empty:
        for _, row in ranking_df.iterrows():
            sym = row["币种"] + "USDT"
            if sym in st.session_state.trader.holdings:
                current_prices[sym] = row["价格"]
    for sym in list(st.session_state.trader.holdings.keys()):
        if sym not in current_prices:
            try:
                latest = get_klines_cached(sym, "1h", limit=1)
                if latest is not None and len(latest) > 0:
                    current_prices[sym] = latest["close"].iloc[-1]
                else:
                    current_prices[sym] = st.session_state.trader.holdings[sym]["avg_price"]
            except Exception:
                current_prices[sym] = st.session_state.trader.holdings[sym]["avg_price"]
    st.session_state.current_prices = current_prices

# ---------- 账户表现 ----------
st.markdown("---")
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
        st.download_button("📊 下载交易记录", trades_csv, "trades.csv", "text/csv")
    st.download_button("📈 下载账户表现", perf_csv, "performance.csv", "text/csv")

# ---------- 详细交易明细 ----------
with st.expander("📊 详细交易盈亏明细", expanded=False):
    # 手动刷新持仓价格按钮
    col_btn_refresh, _ = st.columns([1, 5])
    with col_btn_refresh:
        if st.button("🔄 刷新持仓价格", key="refresh_holdings_price"):
            new_prices = {}
            for sym in st.session_state.trader.holdings.keys():
                price = None
                if not ranking_df.empty:
                    row = ranking_df[ranking_df["币种"] + "USDT" == sym]
                    if not row.empty:
                        price = row.iloc[0]["价格"]
                if price is None:
                    last_k = get_klines_cached(sym, "1h", limit=1)
                    if last_k is not None and len(last_k) > 0:
                        price = last_k["close"].iloc[-1]
                if price:
                    new_prices[sym] = price
            if new_prices:
                if "current_prices" not in st.session_state:
                    st.session_state.current_prices = {}
                st.session_state.current_prices.update(new_prices)
                st.toast("✅ 持仓价格已刷新")
                st.rerun()
            else:
                st.toast("❌ 无法获取最新价格，请稍后重试")

    if st.session_state.trader.holdings:
        st.subheader("📌 当前持仓 (未平仓)")
        holdings_data = []
        total_margin = 0.0
        total_unrealized = 0.0
        funding_rates = {}
        for sym in st.session_state.trader.holdings.keys():
            fr = get_current_funding_rate(sym)
            if fr:
                funding_rates[sym] = fr

        for sym, pos in st.session_state.trader.holdings.items():
            current_price = current_prices.get(sym, pos["avg_price"])
            if pos["side"] == "LONG":
                unrealized_pnl = (current_price - pos["avg_price"]) * pos["quantity"]
                unrealized_pnl_pct = (current_price / pos["avg_price"] - 1) * 100
            else:
                unrealized_pnl = (pos["avg_price"] - current_price) * pos["quantity"]
                unrealized_pnl_pct = (1 - current_price / pos["avg_price"]) * 100
            margin = pos.get("margin", pos["avg_price"] * pos["quantity"] / pos.get("leverage", 1))
            total_margin += margin
            total_unrealized += unrealized_pnl

            fr_data = funding_rates.get(sym)
            if fr_data:
                funding_rate_pct = fr_data * 100
                notional = pos["notional"]
                estimated_funding = notional * fr_data
                funding_str = f"{funding_rate_pct:.4f}%"
                if pos["side"] == "LONG":
                    funding_cost_str = f"{estimated_funding:+.4f} U"
                else:
                    funding_cost_str = f"{-estimated_funding:+.4f} U"
            else:
                funding_str = "N/A"
                funding_cost_str = "N/A"

            holdings_data.append({
                "币种": sym,
                "方向": pos["side"],
                "开仓价": round(pos["avg_price"], 6),
                "当前价": round(current_price, 6),
                "数量": pos["quantity"],
                "占用保证金(USDT)": round(margin, 2),
                "浮动盈亏(USDT)": round(unrealized_pnl, 2),
                "盈亏%": f"{unrealized_pnl_pct:+.2f}%",
                "止损价": round(pos["stop_loss"], 6),
                "止盈价": round(pos["take_profit"], 6),
                "杠杆": pos.get("leverage", 1),
                "资金费率": funding_str,
                "预估资金费": funding_cost_str
            })
        st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)
        st.write(f"**合计** | 占用保证金: {total_margin:.2f} U | 浮动盈亏: {total_unrealized:+.2f} U")

        # 为每个持仓币种单独生成强制平仓按钮
        st.subheader("🛒 强制平仓")
        num_holdings = len(st.session_state.trader.holdings)
        cols_per_row = 3
        rows = (num_holdings + cols_per_row - 1) // cols_per_row
        for row in range(rows):
            col_btns = st.columns(cols_per_row)
            for col_idx in range(cols_per_row):
                idx = row * cols_per_row + col_idx
                if idx >= num_holdings:
                    break
                sym = list(st.session_state.trader.holdings.keys())[idx]
                pos = st.session_state.trader.holdings[sym]
                current_price = current_prices.get(sym, pos["avg_price"])
                with col_btns[col_idx]:
                    st.caption(f"{sym} | 当前价: {current_price:.6f}")
                    if st.button(f"❌ 强制平仓 {sym}", key=f"force_close_single_{sym}"):
                        price = None
                        if not ranking_df.empty:
                            row = ranking_df[ranking_df["币种"] + "USDT" == sym]
                            if not row.empty:
                                price = row.iloc[0]["价格"]
                        if price is None:
                            last_k = get_klines_cached(sym, "1h", limit=1)
                            if last_k is not None and len(last_k) > 0:
                                price = last_k["close"].iloc[-1]
                        if price is None:
                            st.toast(f"❌ 无法获取 {sym} 的最新价格，平仓取消")
                        else:
                            success, pnl, msg = st.session_state.trader.force_close_position(sym, price)
                            if success:
                                st.session_state.adaptive_learner.record_trade({
                                    "symbol": sym,
                                    "pnl": pnl,
                                    "timestamp": now_cn()
                                })
                                save_trader_state()
                                st.toast(f"✅ {msg}")
                                st.rerun()
                            else:
                                st.toast(f"❌ 平仓失败: {msg}")
    else:
        st.info("📭 当前无持仓")

    if st.session_state.trader.trades:
        closed_trades = [t for t in st.session_state.trader.trades if t.get("action") == "CLOSE"]
        if closed_trades:
            st.subheader("📜 历史平仓记录")
            df_trades = pd.DataFrame(closed_trades)
            show_cols = ["timestamp", "symbol", "action", "entry_price", "exit_price", "quantity", "margin", "pnl", "funding_cost", "reason"]
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
            st.warning("数据不足（少于100根K线）")
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
            current_params = {
                "min_score": min_score,
                "risk_pct": risk_pct * 100,
                "stop_loss_pct": stop_loss_pct * 100,
                "take_profit_pct": take_profit_pct * 100
            }
            new_params, reason = st.session_state.adaptive_learner.adapt_params(current_params)
            if new_params != current_params:
                st.session_state.min_score = new_params["min_score"]
                st.session_state.risk_pct = new_params["risk_pct"]
                st.session_state.stop_loss_pct = new_params.get("stop_loss_pct", stop_loss_pct * 100)
                st.session_state.take_profit_pct = new_params.get("take_profit_pct", take_profit_pct * 100)
                st.success(f"参数已调整: {reason}")
                st.rerun()
            else:
                st.info(reason)

# ---------- 每日总结 ----------
with st.expander("📋 每日总结报告", expanded=False):
    if st.button("生成今日报告", key="gen_report"):
        summarizer = DailySummarizer(
            st.session_state.trader,
            df=df,
            ranking_df=ranking_df,
            current_prices=current_prices
        )
        st.session_state.last_report = summarizer.generate()
    if "last_report" in st.session_state:
        st.markdown(st.session_state.last_report)
    else:
        st.info("点击上方按钮生成报告")

# ---------- 实时风控事件 ----------
with st.expander("🚨 实时风控事件", expanded=False):
    if st.button("刷新持仓检查", key="refresh_positions"):
        if df is not None:
            closed = st.session_state.trader.update_positions({selected_symbol: df["close"].iloc[-1]})
            if closed:
                for c in closed:
                    st.session_state.adaptive_learner.record_trade({
                        "symbol": c["symbol"],
                        "pnl": c["pnl"],
                        "timestamp": now_cn()
                    })
                save_trader_state()
                for c in closed:
                    st.write(f"📢 {c['symbol']} {c['reason']} 平仓, 盈亏 {c['pnl']:+.2f} U")
            else:
                st.info("无平仓事件")

# ---------- 自动刷新 ----------
if st.session_state.get("auto_refresh", False):
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
