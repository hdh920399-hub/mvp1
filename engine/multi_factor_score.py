import pandas as pd
import numpy as np
from data.binance import get_open_interest, get_funding_rate, get_top_long_short_ratio

class MultiFactorScorer:
    """四维度多因子评分引擎"""
    
    def __init__(self, df, price_now, symbol, volume_series, change_24h):
        self.df = df
        self.price_now = price_now
        self.symbol = symbol
        self.volume_series = volume_series
        self.change_24h = change_24h
        self.close = df["close"]
        self.high = df["high"]
        self.low = df["low"]
        self.volume = df["volume"]
        
        # 权重配置（百分比）
        self.weight_trend = 35
        self.weight_momentum = 25
        self.weight_volume = 15
        self.weight_sentiment = 25
        
        # 因子贡献值
        self.trend_score = 0
        self.momentum_score = 0
        self.volume_score = 0
        self.sentiment_score = 0
        
        # 因子详细解释
        self.factors_detail = []

    def calculate_rsi(self, period=14):
        delta = self.close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1], rsi

    def calculate_macd(self):
        ema12 = self.close.ewm(span=12, adjust=False).mean()
        ema26 = self.close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        return macd_line, signal_line, macd_hist

    def calculate_adx(self, period=14):
        high, low, close = self.high, self.low, self.close
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-6)
        adx = dx.rolling(period).mean()
        return adx.iloc[-1], atr.iloc[-1]

    def calculate_mfi(self, period=14):
        typical_price = (self.high + self.low + self.close) / 3
        money_flow = typical_price * self.volume
        positive_flow = money_flow.where(typical_price.diff() > 0, 0)
        negative_flow = money_flow.where(typical_price.diff() < 0, 0)
        mfi = 100 - (100 / (1 + positive_flow.rolling(period).sum() / 
                           negative_flow.rolling(period).sum()))
        return mfi.iloc[-1]

    # ---------- 趋势因子 ----------
    def calc_trend_factor(self):
        ma20 = self.close.rolling(20).mean().iloc[-1]
        ma50 = self.close.rolling(50).mean().iloc[-1]
        ma200 = self.close.rolling(200).mean().iloc[-1] if len(self.df) >= 200 else ma50

        if self.price_now > ma20 > ma50 > ma200:
            self.trend_score += 20
            self.factors_detail.append("✅ 完全多头排列 (+20)")
        elif self.price_now > ma20 and self.price_now > ma50:
            self.trend_score += 12
            self.factors_detail.append("✅ 价格在均线上方 (+12)")
        elif self.price_now < ma20 < ma50 < ma200:
            self.trend_score -= 20
            self.factors_detail.append("❌ 完全空头排列 (-20)")
        elif self.price_now < ma20 and self.price_now < ma50:
            self.trend_score -= 12
            self.factors_detail.append("❌ 价格在均线下方 (-12)")

        # 价格相对MA20位置
        ma20_pos = (self.price_now - ma20) / ma20
        if ma20_pos > 0.03:
            self.trend_score += 8
            self.factors_detail.append(f"📈 价格高于MA20 {ma20_pos:.1%} (+8)")
        elif ma20_pos < -0.03:
            self.trend_score -= 8
            self.factors_detail.append(f"📉 价格低于MA20 {abs(ma20_pos):.1%} (-8)")

        adx, _ = self.calculate_adx()
        if adx > 40:
            self.trend_score += 10
            self.factors_detail.append(f"🔥 ADX={adx:.1f} 极强趋势 (+10)")
        elif adx > 25:
            self.trend_score += 7
            self.factors_detail.append(f"📊 ADX={adx:.1f} 强趋势 (+7)")
        elif adx > 20:
            self.trend_score += 3
            self.factors_detail.append(f"⚡ ADX={adx:.1f} 弱趋势 (+3)")
        else:
            self.factors_detail.append(f"🌀 ADX={adx:.1f} 无趋势 (0)")

    # ---------- 动量因子 ----------
    def calc_momentum_factor(self):
        rsi_val, _ = self.calculate_rsi()
        _, _, macd_hist = self.calculate_macd()

        if rsi_val < 25:
            self.momentum_score += 25
            self.factors_detail.append(f"🟢 RSI={rsi_val:.1f} 极端超卖 (+25)")
        elif rsi_val > 75:
            self.momentum_score -= 25
            self.factors_detail.append(f"🔴 RSI={rsi_val:.1f} 极端超买 (-25)")
        elif rsi_val < 35:
            self.momentum_score += 15
            self.factors_detail.append(f"🟢 RSI={rsi_val:.1f} 超卖区 (+15)")
        elif rsi_val > 65:
            self.momentum_score -= 15
            self.factors_detail.append(f"🔴 RSI={rsi_val:.1f} 超买区 (-15)")
        else:
            self.factors_detail.append(f"⚪ RSI={rsi_val:.1f} 中性区 (0)")

        if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-2] <= 0:
            self.momentum_score += 15
            self.factors_detail.append("✅ MACD金叉 (+15)")
        elif macd_hist.iloc[-1] < 0 and macd_hist.iloc[-2] >= 0:
            self.momentum_score -= 15
            self.factors_detail.append("❌ MACD死叉 (-15)")
        elif macd_hist.iloc[-1] > 0:
            self.momentum_score += 6
            self.factors_detail.append("📈 MACD柱为正 (+6)")
        elif macd_hist.iloc[-1] < 0:
            self.momentum_score -= 6
            self.factors_detail.append("📉 MACD柱为负 (-6)")

    # ---------- 成交量因子 ----------
    def calc_volume_factor(self):
        avg_volume = self.volume_series.rolling(20).mean().iloc[-1]
        vol_ratio = self.volume_series.iloc[-1] / avg_volume if avg_volume > 0 else 1

        if vol_ratio > 2.0:
            self.volume_score += 10
            self.factors_detail.append(f"🔥 成交量巨量放大 ({vol_ratio:.1f}x) (+10)")
        elif vol_ratio > 1.5:
            self.volume_score += 7
            self.factors_detail.append(f"📊 成交量显著放大 ({vol_ratio:.1f}x) (+7)")
        elif vol_ratio > 1.2:
            self.volume_score += 4
            self.factors_detail.append(f"📈 成交量温和放大 ({vol_ratio:.1f}x) (+4)")
        else:
            self.factors_detail.append(f"⚪ 成交量正常 ({vol_ratio:.1f}x)")

        mfi = self.calculate_mfi()
        if mfi < 20 and self.momentum_score > 0:
            self.volume_score += 5
            self.factors_detail.append(f"💰 MFI={mfi:.1f} 超卖+放量 (+5)")
        elif mfi > 80 and self.momentum_score < 0:
            self.volume_score -= 5
            self.factors_detail.append(f"⚠️ MFI={mfi:.1f} 超买+放量 (-5)")

    # ---------- 市场情绪因子 ----------
    def calc_sentiment_factor(self):
        try:
            oi = get_open_interest(self.symbol)
            funding = get_funding_rate(self.symbol)
            ls_ratio = get_top_long_short_ratio(self.symbol)
        except:
            oi, funding, ls_ratio = 0, 0, 1.0

        # 持仓量贡献
        if oi > 5_000_000:  # 500万美金以上高OI
            self.sentiment_score += 5
            self.factors_detail.append(f"🔥 高持仓量 OI=${oi/1e6:.1f}M (+5)")

        # 资金费率贡献
        funding_pct = funding * 100
        if funding < -0.05:
            self.sentiment_score += 5
            self.factors_detail.append(f"📉 资金费率 {funding_pct:.3f}% (空头拥挤) (+5)")
        elif funding > 0.1:
            self.sentiment_score -= 5
            self.factors_detail.append(f"📈 资金费率 {funding_pct:.3f}% (多头拥挤) (-5)")
        elif funding < -0.01:
            self.sentiment_score += 2
            self.factors_detail.append(f"📉 资金费率 {funding_pct:.3f}% (略偏负) (+2)")
        elif funding > 0.03:
            self.sentiment_score -= 2
            self.factors_detail.append(f"📈 资金费率 {funding_pct:.3f}% (略偏高) (-2)")

        # 多空比贡献
        if ls_ratio > 1.5:
            self.sentiment_score -= 4
            self.factors_detail.append(f"⚖️ 多空比 {ls_ratio:.2f} (多头拥挤) (-4)")
        elif ls_ratio < 0.7:
            self.sentiment_score += 4
            self.factors_detail.append(f"⚖️ 多空比 {ls_ratio:.2f} (空头拥挤) (+4)")

        # 24h涨跌幅惩罚
        if abs(self.change_24h) > 30:
            self.sentiment_score -= 8
            self.factors_detail.append(f"⚠️ 24h振幅 {abs(self.change_24h):.1f}% 过大，风险较高 (-8)")

    # ---------- 综合评分 ----------
    def calculate_total_score(self):
        self.calc_trend_factor()
        self.calc_momentum_factor()
        self.calc_volume_factor()
        self.calc_sentiment_factor()

        weighted_trend = self.trend_score * (self.weight_trend / 100)
        weighted_momentum = self.momentum_score * (self.weight_momentum / 100)
        weighted_volume = self.volume_score * (self.weight_volume / 100)
        weighted_sentiment = self.sentiment_score * (self.weight_sentiment / 100)

        total_score = weighted_trend + weighted_momentum + weighted_volume + weighted_sentiment
        total_score = max(0, min(100, int(total_score)))

        # 信号方向
        if total_score >= 60:
            signal_text = "🟢 强烈做多" if total_score >= 75 else "🟢 做多"
            direction = "LONG"
        elif total_score <= 40:
            signal_text = "🔴 强烈做空" if total_score <= 25 else "🔴 做空"
            direction = "SHORT"
        else:
            signal_text = "⚪ 观望"
            direction = "NEUTRAL"

        # 动态杠杆（基于ATR波动率）
        _, atr = self.calculate_adx()
        volatility_pct = atr / self.price_now * 100
        if volatility_pct > 4:
            leverage = 1
        elif volatility_pct > 2:
            leverage = 3
        else:
            leverage = 5

        analysis = "；".join(self.factors_detail) + f"。综合评分：{total_score}分。建议杠杆：{leverage}x。方向：{direction}。"

        # 保存RSI值用于展示
        rsi_val, _ = self.calculate_rsi()

        return {
            "total_score": total_score,
            "direction": direction,
            "signal_text": signal_text,
            "leverage": leverage,
            "analysis": analysis,
            "rsi": round(rsi_val, 1),
            "factors": self.factors_detail
        }
