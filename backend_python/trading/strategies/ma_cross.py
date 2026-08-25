"""
Стратегия MA Cross + RSI — простая, понятная база.

BUY: быстрая MA пересекла медленную снизу И RSI не в перекупленности.
SELL: быстрая MA пересекла медленную сверху ИЛИ RSI в перекупленности.
Размер позиции = % от баланса × confidence (движок ещё раз проверит минимум
и комиссии, поэтому тут можно давать "желаемое", а не точный лимит).
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from ..base import Action, MarketFrame, TradeSignal, Strategy
from ..registry import register_strategy

logger = logging.getLogger(__name__)


def _sma(values: list[float], period: int) -> float:
    if len(values) < period:
        return float(values[-1]) if values else 0.0
    return float(np.mean(values[-period:]))


def _rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes[-(period + 1):])
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = gains.mean()
    avg_loss = losses.mean()
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100.0 - (100.0 / (1.0 + rs)))


@register_strategy
class MACrossStrategy(Strategy):
    name = "ma_cross"
    description = "Пересечение скользящих средних + RSI (базовая, без ИИ)"
    weight = 1.0
    enabled_by_default = True

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.fast = int(self.config.get("fast_period", 9))
        self.slow = int(self.config.get("slow_period", 21))
        self.rsi_period = int(self.config.get("rsi_period", 14))
        self.rsi_overbought = float(self.config.get("rsi_overbought", 70.0))
        self.rsi_oversold = float(self.config.get("rsi_oversold", 30.0))
        self.position_pct = float(self.config.get("position_pct", 0.5))
        self.take_profit_pct = float(self.config.get("take_profit_pct", 0.02))
        self.stop_loss_pct = float(self.config.get("stop_loss_pct", 0.015))
        self.min_data = max(self.slow + 2, 30)

    async def analyze(self, frame: MarketFrame) -> Optional[TradeSignal]:
        closes = frame.closes
        if len(closes) < self.min_data:
            return None

        fast_now = _sma(closes, self.fast)
        slow_now = _sma(closes, self.slow)
        fast_prev = _sma(closes[:-1], self.fast)
        slow_prev = _sma(closes[:-1], self.slow)
        rsi = _rsi(closes, self.rsi_period)

        crossed_up = fast_prev <= slow_prev and fast_now > slow_now
        crossed_down = fast_prev >= slow_prev and fast_now < slow_now

        bal = frame.context.get("balance_usdt", 0.0)
        size = bal * self.position_pct if bal > 0 else 0.0

        trend_up = fast_now > slow_now

        # BUY пока тренд вверх (fast > slow). На сильном тренде RSI всегда
        # высокий — это нормально, поэтому RSI НЕ блокирует вход, а лишь
        # снижает уверенность, чтобы не входить на самом экстремуме.
        if trend_up:
            # чем ближе RSI к 100, тем меньше уверенность (осторожнее)
            overbought_penalty = max(0.0, (rsi - self.rsi_overbought) / 30.0)
            conf = max(0.4, 0.9 - overbought_penalty)
            return TradeSignal(
                symbol=frame.symbol, action=Action.BUY, confidence=conf,
                amount=size, strategy_name=self.name,
                take_profit=frame.close * (1 + self.take_profit_pct),
                stop_loss=frame.close * (1 - self.stop_loss_pct),
                note=f"trend UP (fast>slow), RSI={rsi:.1f}",
            )

        # SELL только при реальном развороте вниз (быстрая MA ушла ниже медленной).
        if crossed_down or (not trend_up and rsi < self.rsi_oversold):
            return TradeSignal(
                symbol=frame.symbol, action=Action.SELL, confidence=0.7,
                amount=size, strategy_name=self.name,
                note=f"trend DOWN / RSI oversold, RSI={rsi:.1f}",
            )
        return None
