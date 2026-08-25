"""
Стратегия AI News Sentiment — ЗАГОТОВКА под нейросеть.

Идея (твоя): "в перспективе читая сфотки новостей нейронкой и учитывая это".
Реализуем контракт NewsAnalyzer: он принимает текст/фото новостей и
возвращает сентимент (-1..+1) + краткое описание. По умолчанию стоит
ЗАГЛУШКА (random/rule-based), чтобы архитектура была рабочей без ollama.
Позже подключаем реальный LLM через /projects/ollama (OllamaClient).

Стратегия: если сентимент сильно положительный — BUY, отрицательный — SELL.
Вес стратегии выше, т.к. это "интеллектуальный" сигнал.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from ..base import Action, MarketFrame, TradeSignal, Strategy
from ..registry import register_strategy

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Интерфейс анализатора новостей. Заменим на ollama-реализацию позже."""

    async def analyze(self, texts: List[str], images_b64: Optional[List[str]] = None) -> Dict[str, Any]:
        """Вернуть {'sentiment': -1..1, 'summary': str}."""
        # ЗАГЛУШКА: простой эвристический сентимент по ключевым словам.
        positive = ["рост", "buy", "bull", "взлет", "прибыль", "breakout", "🚀"]
        negative = ["падение", "sell", "bear", "обвал", "убыток", "crash", "🔻"]
        score = 0.0
        for t in texts:
            tl = t.lower()
            score += sum(1 for w in positive if w in tl)
            score -= sum(1 for w in negative if w in tl)
        if score > 0:
            return {"sentiment": min(1.0, score * 0.3), "summary": "позитивные сигналы"}
        if score < 0:
            return {"sentiment": max(-1.0, score * 0.3), "summary": "негативные сигналы"}
        return {"sentiment": 0.0, "summary": "нейтрально"}


@register_strategy
class AINewsStrategy(Strategy):
    name = "ai_news"
    description = "Анализ новостей нейросетью (заготовка под Ollama/LLM)"
    weight = 1.5
    enabled_by_default = False  # включаем вручную, когда готов LLM-бэкенд

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.analyzer = NewsAnalyzer()
        self.threshold = float(self.config.get("sentiment_threshold", 0.3))
        self.position_pct = float(self.config.get("position_pct", 0.4))

    async def analyze(self, frame: MarketFrame) -> Optional[TradeSignal]:
        # Берём новости из контекста (их туда подложит движок/сборщик новостей)
        news: List[str] = frame.context.get("news", [])
        if not news:
            return None

        result = await self.analyzer.analyze(news)
        sent = result.get("sentiment", 0.0)
        if abs(sent) < self.threshold:
            return None

        bal = frame.context.get("balance_usdt", 0.0)
        size = bal * self.position_pct if bal > 0 else 0.0
        action = Action.BUY if sent > 0 else Action.SELL

        return TradeSignal(
            symbol=frame.symbol, action=action,
            confidence=min(1.0, abs(sent) + 0.2),
            amount=size, strategy_name=self.name,
            note=f"news sentiment={sent:.2f}: {result.get('summary')}",
            meta={"sentiment": sent},
        )
