"""
StrategyEngine — ядро принятия решений.

Собирает сигналы от всех ВКЛЮЧЁННЫХ стратегий, делает взвешенный
ансамбль (совокупность данных) и выдаёт одно финальное решение с
обязательной проверкой КОМИССИЙ и защитой МИКРО-ДЕПОЗИТА.

Принцип для малых сумм (от $2):
  - сделка имеет смысл, только если ожидаемый профит > комиссия × буфер
  - размер позиции ограничен % от баланса и абсолютным минимумом
  - при падении баланса ниже порога — торговля на паузу (kill-switch)
"""
from __future__ import annotations

from typing import Dict, List, Optional
import logging

from .base import Action, MarketFrame, TradeSignal, Strategy
from .registry import StrategyRegistry

logger = logging.getLogger(__name__)


class StrategyEngine:
    def __init__(self, registry: StrategyRegistry, config: Optional[dict] = None):
        self.registry = registry
        self.config = config or {}

        # --- параметры торговли / риска (важны для микро-сумм) ---
        self.min_trade_usdt = float(self.config.get("min_trade_usdt", 2.0))
        self.max_position_pct = float(self.config.get("max_position_pct", 0.95))
        self.commission_rate = float(self.config.get("commission_rate", 0.001))
        # сделка только если ожид. профит покрывает комиссию × этот буфер
        self.commission_buffer = float(self.config.get("commission_buffer", 3.0))
        self.take_profit_pct = float(self.config.get("take_profit_pct", 0.02))
        self.stop_loss_pct = float(self.config.get("stop_loss_pct", 0.015))
        # kill-switch: если баланс < этого значения (USDT) — пауза
        self.min_balance_usdt = float(self.config.get("min_balance_usdt", 1.0))

        self.last_signals: Dict[str, TradeSignal] = {}

    async def run_cycle(self, frame: MarketFrame,
                        balance_usdt: float = 0.0) -> Optional[TradeSignal]:
        """Один цикл: собрать сигналы стратегий -> ансамбль -> финальное решение."""
        # Kill-switch для микро-депозита
        if balance_usdt > 0 and balance_usdt < self.min_balance_usdt:
            logger.warning(f"⛔ Kill-switch: баланс {balance_usdt:.2f} USDT < "
                           f"{self.min_balance_usdt:.2f} — торговля на паузе")
            return None

        strategies = self.registry.active_strategies(self.config)
        if not strategies:
            return None

        collected: List[TradeSignal] = []
        for strat in strategies:
            try:
                if strat.allowed_symbols() and frame.symbol not in strat.allowed_symbols():
                    continue
                sig = await strat.analyze(frame)
                if sig:
                    collected.append(sig)
                    self.last_signals[strat.name] = sig
            except Exception as e:
                logger.error(f"Ошибка стратегии {strat.name}: {e}")

        if not collected:
            return None

        final = self._ensemble(collected, balance_usdt)
        if final is None:
            return None

        # прокидываем баланс в сигнал, чтобы фильтры могли ограничить размер
        if balance_usdt > 0:
            final.meta["balance_usdt"] = balance_usdt

        # Жёсткая проверка: хватает ли суммы и окупаются ли комиссии
        if not self._passes_filters(final, frame.close):
            return None

        return final

    # --- ансамбль (взвешенное голосование) ---
    def _ensemble(self, signals: List[TradeSignal],
                  balance_usdt: float) -> Optional[TradeSignal]:
        buy_w = 0.0
        sell_w = 0.0
        best_buy: Optional[TradeSignal] = None
        best_sell: Optional[TradeSignal] = None

        for s in signals:
            w = self.registry._weights.get(s.strategy_name, 1.0)
            if s.action == Action.BUY:
                buy_w += w * s.confidence
                if best_buy is None or s.confidence > best_buy.confidence:
                    best_buy = s
            elif s.action == Action.SELL:
                sell_w += w * s.confidence
                if best_sell is None or s.confidence > best_sell.confidence:
                    best_sell = s

        if buy_w > sell_w and best_buy:
            return best_buy
        if sell_w > buy_w and best_sell:
            return best_sell
        return None

    # --- фильтры: комиссии + микро-суммы ---
    def _passes_filters(self, sig: TradeSignal, price: float) -> bool:
        bal = sig.meta.get("balance_usdt", 0.0)

        # Если сигнал есть, но сумма меньше минимума — попробуем поднять до
        # минимума в рамках допустимого % от баланса (важно для микро-депозитов).
        if sig.amount < self.min_trade_usdt and bal > 0:
            raised = min(self.min_trade_usdt, bal * self.max_position_pct)
            if raised >= self.min_trade_usdt:
                sig.amount = raised

        # минимальная сумма сделки
        if sig.amount < self.min_trade_usdt:
            logger.info(f"Сигнал {sig.strategy_name}: сумма {sig.amount:.2f} < "
                        f"минимума {self.min_trade_usdt:.2f} — пропуск")
            return False

        # комиссия туда-обратно должна окупаться потенциальным профитом
        round_trip_fee = sig.amount * self.commission_rate * 2
        expected_profit = sig.amount * max(
            self.take_profit_pct if sig.action == Action.BUY else self.stop_loss_pct, 0.0
        )
        if expected_profit < round_trip_fee * self.commission_buffer:
            logger.info(f"Сигнал {sig.strategy_name}: ожид. профит {expected_profit:.4f} "
                        f"не покрывает комиссии {round_trip_fee:.4f}×{self.commission_buffer} — пропуск")
            return False

        # размер позиции в рамках лимита от баланса (если баланс известен)
        if bal:
            cap = bal * self.max_position_pct
            if sig.amount > cap:
                sig.amount = cap
        return True

    def set_balance_context(self, sig: TradeSignal, balance_usdt: float):
        sig.meta["balance_usdt"] = balance_usdt
