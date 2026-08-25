"""
Стратегия AI News Sentiment — анализ новостей нейросетью.

Подключается к локальному LLM-серверу (llama.cpp / LM Studio / ollama)
через универсальный trading.llm.LLMClient. По умолчанию использует
LM Studio на :1234 (внутри — llama.cpp server). Чтобы переключить на
чистый llama.cpp: запусти `./llama-server -m model.gguf --port 8080`
и задай переменную TGRODER_LLM_URL=http://localhost:8080.

Возможности (гибче ollama):
  - тонкая настройка temperature/top_p/repeat_penalty
  - VISION: читаем фото новостей (base64) — модель типа llama3.2-vision
  - любые GGUF-модели, параллельные слоты

Стратегия: сильный позитивный сентимент -> BUY, негатив -> SELL.
Вес выше базовых, т.к. это "интеллектуальный" сигнал.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from ..base import Action, MarketFrame, TradeSignal, Strategy
from ..registry import register_strategy
from ..llm import LLMClient

logger = logging.getLogger(__name__)


@register_strategy
class AINewsStrategy(Strategy):
    name = "ai_news"
    description = "Анализ новостей нейросетью (LLM: llama.cpp/LM Studio/ollama)"
    weight = 1.5
    enabled_by_default = False  # включаем вручную, когда готов LLM-бэкенд

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.position_pct = float(self.config.get("position_pct", 0.4))
        self.sentiment_threshold = float(self.config.get("sentiment_threshold", 0.3))
        # Ленивая инициализация клиента (не при старте, а при первом анализе)
        self._llm: Optional[LLMClient] = None

    def _get_llm(self) -> Optional[LLMClient]:
        if self._llm is None:
            try:
                self._llm = LLMClient()
            except Exception as e:
                logger.warning(f"ai_news: LLM-клиент недоступен: {e}")
                return None
        return self._llm

    async def analyze(self, frame: MarketFrame) -> Optional[TradeSignal]:
        news: List[str] = frame.context.get("news", [])
        if not news:
            return None

        llm = self._get_llm()
        if llm is None:
            # Фолбэк: простая эвристика, если LLM не поднят
            return self._heuristic(news, frame)

        result = llm.analyze_sentiment(news)
        sent = result.get("sentiment", 0.0)
        if abs(sent) < self.sentiment_threshold:
            return None

        bal = frame.context.get("balance_usdt", 0.0)
        size = bal * self.position_pct if bal > 0 else 0.0
        action = Action.BUY if sent > 0 else Action.SELL
        return TradeSignal(
            symbol=frame.symbol, action=action,
            confidence=min(1.0, abs(sent) + 0.2),
            amount=size, strategy_name=self.name,
            note=f"LLM sentiment={sent:.2f}: {result.get('summary')}",
            meta={"sentiment": sent, "symbols": result.get("symbols", [])},
        )

    def _heuristic(self, news: List[str], frame: MarketFrame) -> Optional[TradeSignal]:
        """Эвристический фолбэк без LLM (по ключевым словам)."""
        positive = ["рост", "buy", "bull", "взлет", "прибыль", "breakout", "🚀"]
        negative = ["падение", "sell", "bear", "обвал", "убыток", "crash", "🔻"]
        score = 0.0
        for t in news:
            tl = t.lower()
            score += sum(1 for w in positive if w in tl)
            score -= sum(1 for w in negative if w in tl)
        if abs(score) < 1:
            return None
        sent = max(-1.0, min(1.0, score * 0.3))
        if abs(sent) < self.sentiment_threshold:
            return None
        bal = frame.context.get("balance_usdt", 0.0)
        size = bal * self.position_pct if bal > 0 else 0.0
        action = Action.BUY if sent > 0 else Action.SELL
        return TradeSignal(
            symbol=frame.symbol, action=action,
            confidence=min(1.0, abs(sent) + 0.2), amount=size,
            strategy_name=self.name, note=f"heuristic sentiment={sent:.2f}",
            meta={"sentiment": sent},
        )
