import streamlit as st
from scanner.multi import scan_cheap_coins_with_signal

def auto_trade(trader, max_price=1.0, max_positions=5, risk_pct=0.1,
               long_min_score=60, short_min_score=60,
               stop_loss_pct=None, take_profit_pct=None):
    """
    自动交易：从做多榜和做空榜中选取评分最高的币种，独立阈值判断
    """
    result = {"trades": []}
    if len(trader.holdings) >= max_positions:
        st.toast(f"⚠️ 已达最大持仓数 {max_positions}")
        return result

    # 获取两个排行榜
    long_ranking_df, short_ranking_df, total = scan_cheap_coins_with_signal(max_price, limit=20)
    
    if long_ranking_df.empty and short_ranking_df.empty:
        st.toast("❌ 未扫描到任何币种")
        return result

    # 构建候选列表：做多榜中评分 >= long_min_score 的币种
    candidates = []
    for _, row in long_ranking_df.iterrows():
        score = row["做多分"]
        if score >= long_min_score:
            candidates.append({
                "symbol": row["币种"] + "USDT",
                "score": score,
                "price": row["价格"],
                "side": "LONG",
                "signal": row["做多信号"]
            })
    
    # 做空榜中评分 >= short_min_score 的币种（注意：做空分越高越适合做空）
    for _, row in short_ranking_df.iterrows():
        score = row["做空分"]
        if score >= short_min_score:
            candidates.append({
                "symbol": row["币种"] + "USDT",
                "score": score,
                "price": row["价格"],
                "side": "SHORT",
                "signal": row["做空信号"]
            })
    
    # 按分数降序排序
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    total_asset = trader.get_total_asset()
    stop_ratio = stop_loss_pct if stop_loss_pct is not None else trader.stop_loss_pct
    if stop_ratio <= 0:
        stop_ratio = 0.02

    for cand in candidates:
        if len(trader.holdings) >= max_positions:
            break
        if cand["symbol"] in trader.holdings:
            continue
        
        max_loss = total_asset * risk_pct
        notional = max_loss / stop_ratio
        notional = max(10.0, notional)
        leverage = 5  # 默认杠杆，可从AI分析获取
        
        if cand["side"] == "LONG":
            success, msg = trader.buy(cand["symbol"], cand["price"], notional, leverage=leverage,
                                      stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct)
            action = "BUY"
        else:
            success, msg = trader.short(cand["symbol"], cand["price"], notional, leverage=leverage,
                                        stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct)
            action = "SHORT"
        
        if success:
            result["trades"].append({
                "action": action,
                "symbol": cand["symbol"],
                "price": cand["price"],
                "leverage": leverage,
                "score": cand["score"],
                "side": cand["side"]
            })
            st.toast(f"✅ 自动{cand['side']} {cand['symbol']} @ {cand['price']} (评分:{cand['score']})")
            # 更新总资产（用于下一个开仓）
            total_asset = trader.get_total_asset()
    
    if not result["trades"]:
        st.toast(f"🤖 未找到满足条件的开仓机会 (做多需≥{long_min_score}，做空需≥{short_min_score})")
    return result
