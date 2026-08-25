"""
Пакет стратегий. Импорт любого модуля здесь автоматически регистрирует
стратегию через декоратор @register_strategy. Движок импортирует этот
пакет один раз при старте — и все стратегии оказываются в реестре.

Чтобы добавить новую стратегию любой сложности (ML, паттерны, ИИ-новости):
  1. создай файл в этом каталоге (например, my_strategy.py)
  2. унаследуй Strategy и пометь @register_strategy
  3. импортируй его здесь (или добавь в __all__)
"""

from .ma_cross import MACrossStrategy
from .ai_news import AINewsStrategy

__all__ = ["MACrossStrategy", "AINewsStrategy"]
