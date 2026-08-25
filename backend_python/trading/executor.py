"""
PaperExecutor — симулятор исполнения сделок с учётом КОМИССИЙ.

Позволяет прогонять стратегии на реальных/исторических данных без риска
реальных денег. Критически важно для микро-депозитов: сначала проверяем
стратегию в "песочнице", смотрим чистый PnL (за вычетом комиссий), и только
потом подключаем реальный CCXTExecutor.

Позже добавим CCXTExecutor (реальная биржа по API-ключам пользователя) и
TonConnectExecutor (TON DEX через Mini App). Все наследуют Executor.
"""
from __future__ import annotations

from typing import Optional
import logging
from dataclasses import dataclass, field

from .base import Action, TradeSignal

logger = logging.getLogger(__name__)


@dataclass
class ExecResult:
    ok: bool
    order_id: str = ""
    executed_price: float = 0.0
    fee: float = 0.0
    message: str = ""


class Executor:
    """Базовый исполнитель. Наследуй для реальных бирж/DEX."""
    name = "base"

    async def execute(self, signal: TradeSignal, price: float) -> ExecResult:
        raise NotImplementedError


class PaperExecutor(Executor):
    name = "paper"

    def __init__(self, commission_rate: float = 0.001, starting_usdt: float = 100.0):
        self.commission_rate = commission_rate
        self.cash_usdt = starting_usdt      # свободные средства
        self.position_amount = 0.0          # в базовой валюте актива
        self.position_cost = 0.0            # USDT вложено
        self.trades: list = []
        self.realized_pnl = 0.0
        self._last_price = 0.0

    @property
    def equity(self) -> float:
        pos_val = self.position_amount * self._last_price
        return self.cash_usdt + pos_val

    def set_price(self, price: float):
        self._last_price = price

    async def execute(self, signal: TradeSignal, price: float) -> ExecResult:
        self._last_price = price
        if signal.action == Action.BUY:
            return self._buy(signal, price)
        if signal.action == Action.SELL:
            return self._sell(signal, price)
        return ExecResult(ok=False, message="HOLD — нет действия")

    def _buy(self, signal: TradeSignal, price: float) -> ExecResult:
        spend = min(signal.amount, self.cash_usdt)
        if spend <= 0:
            return ExecResult(ok=False, message="Нет свободных USDT")
        fee = spend * self.commission_rate
        net = spend - fee
        got = net / price
        self.cash_usdt -= spend
        self.position_amount += got
        self.position_cost += spend
        self.trades.append({"side": "BUY", "price": price, "spend": spend, "fee": fee})
        return ExecResult(ok=True, order_id="paper_buy", executed_price=price, fee=fee,
                          message=f"Куплено {got:.6f} по {price:.4f}, комиссия {fee:.4f}")

    def _sell(self, signal: TradeSignal, price: float) -> ExecResult:
        if self.position_amount <= 0:
            return ExecResult(ok=False, message="Нет позиции для продажи")
        # продаём пропорционально запрошенной доле (amount/cost)
        share = min(1.0, signal.amount / self.position_cost) if self.position_cost else 1.0
        sell_amt = self.position_amount * share
        gross = sell_amt * price
        fee = gross * self.commission_rate
        net = gross - fee
        cost_part = self.position_cost * share
        self.realized_pnl += net - cost_part
        self.cash_usdt += net
        self.position_amount -= sell_amt
        self.position_cost -= cost_part
        self.trades.append({"side": "SELL", "price": price, "gross": gross, "fee": fee})
        return ExecResult(ok=True, order_id="paper_sell", executed_price=price, fee=fee,
                          message=f"Продано {sell_amt:.6f} по {price:.4f}, комиссия {fee:.4f}")
