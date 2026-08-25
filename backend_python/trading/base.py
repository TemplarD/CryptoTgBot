"""
Базовые типы и контракты для торговых стратегий TgTrader.

ЕДИНЫЙ КОНТРАКТ: любая стратегия получает MarketFrame и возвращает
TradeSignal (или None). Движок (StrategyEngine) не знает внутренностей
стратегии и может комбинировать сигналы от любого числа стратегий
любой сложности (от простой MA-cross до LLM-анализа новостей).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class MarketFrame:
    """Снимок рынка для одной торговой пары в один момент времени.

    Стратегия получает список таких фреймов (история + текущий) и решает,
    что делать. Поля минимально необходимы и легко расширяются.
    """
    symbol: str
    timeframe: str = "1h"
    # OHLCV-история (старые -> новые). close[-1] — текущая цена.
    timestamps: list[float] = field(default_factory=list)
    opens: list[float] = field(default_factory=list)
    highs: list[float] = field(default_factory=list)
    lows: list[float] = field(default_factory=list)
    closes: list[float] = field(default_factory=list)
    volumes: list[float] = field(default_factory=list)
    # Доп. контекст (курс к USDT, сентимент новостей и т.п.) — нестрого.
    context: Dict[str, Any] = field(default_factory=dict)

    @property
    def close(self) -> float:
        return self.closes[-1] if self.closes else 0.0

    @property
    def has_enough(self, n: int = 2) -> bool:
        return len(self.closes) >= n


@dataclass
class TradeSignal:
    """Решение стратегии. Движок агрегирует сигналы и исполняет их."""
    symbol: str
    action: Action
    confidence: float = 0.0          # 0..1
    amount: float = 0.0              # в базовой валюте (USDT)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_name: str = "unknown"
    note: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def is_actionable(self) -> bool:
        return self.action != Action.HOLD and self.amount > 0


class Strategy:
    """Базовый класс стратегии. Наследуй и реализуй analyze().

    Чтобы добавить новую стратегию любой сложности (включая ИИ/нейросети):
      1. создай файл в trading/strategies/your_strategy.py
      2. унаследуй Strategy
      3. зарегистрируй через @register_strategy() или в registry
    """

    # Имя (уникальное), описание, вес для ансамбля, включена ли по умолчанию
    name: str = "base"
    description: str = ""
    weight: float = 1.0
    enabled_by_default: bool = True

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    async def analyze(self, frame: MarketFrame) -> Optional[TradeSignal]:
        """Вернуть TradeSignal или None (сигнала нет)."""
        raise NotImplementedError

    def allowed_symbols(self) -> Optional[list[str]]:
        """None = все символы; иначе ограниченный список."""
        return None
