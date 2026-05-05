def suggest_position(market_state, risk_level="中", capital=100):
    """计算仓位建议"""
    state_map = {
        "BULL": {"激进": 0.8, "中": 0.6, "保守": 0.4},
        "SIDEWAYS": {"激进": 0.5, "中": 0.3, "保守": 0.2},
        "BEAR": {"激进": 0.2, "中": 0.1, "保守": 0.05}
    }
    
    leverage_map = {
        "BULL": {"激进": 5, "中": 3, "保守": 1},
        "SIDEWAYS": {"激进": 2, "中": 1, "保守": 1},
        "BEAR": {"激进": 1, "中": 1, "保守": 1}
    }
    
    position_pct = state_map.get(market_state, {"激进": 0.3, "中": 0.2, "保守": 0.1}).get(risk_level, 0.3)
    leverage = leverage_map.get(market_state, {"激进": 1, "中": 1, "保守": 1}).get(risk_level, 1)
    
    position_usdt = capital * position_pct
    
    return {
        "仓位比例": f"{position_pct * 100:.0f}%",
        "仓位金额": f"{position_usdt:.0f} USDT",
        "杠杆倍数": leverage,
        "风险等级": risk_level,
        "市场状态": market_state
    }
