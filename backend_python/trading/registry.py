"""
Реестр стратегий — единая точка выбора и управления активными стратегий.

Позволяет:
  - зарегистрировать стратегию (авто при импорте пакета strategies)
  - включать/выключать по имени (из ТГ-команды или Mini App)
  - менять вес (для ансамбля)
  - получить список для UI/API
"""
from __future__ import annotations

from typing import Dict, List, Type, Optional
import logging

from .base import Strategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    def __init__(self):
        self._registry: Dict[str, Type[Strategy]] = {}
        self._enabled: Dict[str, bool] = {}
        self._weights: Dict[str, float] = {}
        self._instances: Dict[str, Strategy] = {}

    # --- регистрация ---
    def register(self, cls: Type[Strategy], enabled: Optional[bool] = None,
                 weight: Optional[float] = None):
        name = cls.name
        if not name or name == "base":
            raise ValueError("Стратегия должна иметь уникальное имя (name)")
        self._registry[name] = cls
        self._enabled[name] = enabled if enabled is not None else cls.enabled_by_default
        self._weights[name] = weight if weight is not None else cls.weight
        logger.info(f"Зарегистрирована стратегия: {name} ({cls.__name__})")

    def register_instance(self, inst: Strategy, enabled: Optional[bool] = None):
        self.register(type(inst), enabled)
        self._instances[inst.name] = inst

    # --- управление ---
    def enable(self, name: str, on: bool = True):
        if name in self._enabled:
            self._enabled[name] = on
            return True
        return False

    def set_weight(self, name: str, weight: float):
        if name in self._weights:
            self._weights[name] = max(0.0, float(weight))
            return True
        return False

    def is_enabled(self, name: str) -> bool:
        return self._enabled.get(name, False)

    # --- доступ ---
    def names(self) -> List[str]:
        return list(self._registry.keys())

    def get_instance(self, name: str, config: Optional[dict] = None) -> Optional[Strategy]:
        if name not in self._registry:
            return None
        if name not in self._instances:
            self._instances[name] = self._registry[name](config)
        return self._instances[name]

    def active_strategies(self, config: Optional[dict] = None) -> List[Strategy]:
        """Возвращает экземпляры ВКЛЮЧЁННЫХ стратегий."""
        out = []
        for name in self._registry:
            if self._enabled.get(name, False):
                out.append(self.get_instance(name, config))
        return out

    def list_for_api(self) -> List[dict]:
        """Для эндпоинта /api/strategies (управление из ТГ/Mini App)."""
        return [
            {
                "name": name,
                "class": cls.__name__,
                "description": cls.description,
                "enabled": self._enabled.get(name, False),
                "weight": self._weights.get(name, cls.weight),
            }
            for name, cls in self._registry.items()
        ]


# Глобальный реестр приложения
registry = StrategyRegistry()


def register_strategy(cls: Type[Strategy]):
    """Декоратор для быстрой регистрации."""
    registry.register(cls)
    return cls
