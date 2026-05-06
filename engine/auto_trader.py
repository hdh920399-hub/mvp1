import streamlit as st
from scanner.multi import scan_cheap_coins_with_signal

def auto_trade(trader, max_price=1.0, max_positions=3, risk_pct=0.1, min_score=20,
               stop_loss_pct=None, take_profit_pct=None):
    """
    自动交易函数 - 方案二：真正控制最大亏损比例
    risk_pct: 单笔最大亏损占当前总资产的比例（例如 0.1 = 10%）
    """
    result = {"trades": []}
    if len(trader.holdings) >= max_positions:
        st.toast(f"⚠️ 已达最大持仓数 {max_positions}")
        return result

    ranking_df, total = scan_cheap_coins_with_signal(max_price, limit=10)
    if ranking_df.empty:
        st.toast("❌ 未扫描到任何低价币")
        return result

    ranking_df = ranking_df.sort_values("评分", ascending=False)
    st.toast(f"🔍 扫描到 {len(ranking_df)} 个币，最高评分: {ranking_df.iloc[0]['评分']}")

    # 获取总资产（用于计算最大亏损）
    total_asset = trader.get_total_asset()
    # 止损幅度（用户设定的百分比）
    stop_ratio = stop_loss_pct if stop_loss_pct is not None else trader.stop_loss_pct
    if stop_ratio <= 0:
        stop_ratio = 0.02

    for _, row in ranking_df.iterrows():
        symbol = row["币种"] + "USDT"
        score = row["评分"]
        price = row["价格"]
        signal_type = row.get("AI信号", "")
        leverage = row.get("建议杠杆", 1)

        if symbol in trader.holdings:
            continue

        if score >= min_score:
            # 最大允许亏损
            max_loss = total_asset * risk_pct
            # 名义价值 = 最大亏损 / 止损幅度
            notional = max_loss / stop_ratio
            # 最小名义价值限制
            notional = max(10.0, notional)

            if "做多" in signal_type:
                success, msg = trader.buy(symbol, price, notional, leverage=leverage,
                                          stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct)
                action = "BUY"
            elif "做空" in signal_type:
                success, msg = trader.short(symbol, price, notional, leverage=leverage,
                                            stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct)
                action = "SHORT"
            else:
                continue

            if success:
                result["trades"].append({
                    "action": action,
                    "symbol": symbol,
                    "price": price,
                    "leverage": leverage,
                    "notional": notional
                })
                st.toast(f"✅ 自动{action} {symbol} @ {price} (信号:{signal_type}, 杠杆:{leverage}x, 名义价值:{notional:.2f}U)")
                return result
    st.toast(f"🤖 未找到评分 ≥ {min_score} 的币种")
    return result
