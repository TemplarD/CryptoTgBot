"""
Универсальный LLM-клиент для TgTrader.

Работает с ЛЮБЫМ OpenAI-совместимым сервером (один и тот же протокол
/v1/chat/completions):
  - LM Studio      -> http://localhost:1234  (внутри использует llama.cpp server)
  - llama.cpp       -> http://localhost:8080  (./llama-server -m model.gguf)
  - Ollama          -> http://localhost:11434  (совместимо с OpenAI API)
  - удалённые API   -> любой прокси

Почему через LM Studio / llama.cpp напрямую, а не только ollama:
  - тонкая настройка (temperature, top_p, repeat_penalty, chat-template)
  - поддержка VISION (llava/llama3.2-vision/Phi-3.5-vision): можно
    "читать фото новостей нейронкой" — передаём base64-картинку в content
  - грузим любые GGUF, параллельные слоты, контроль KV-cache

Железо пользователя: 2× Xeon E5-2666v3, 128GB RAM, слабая видеокарта
(GeForce 7600GS, только монитор) -> инференс идёт на CPU через llama.cpp.
Для тестов берём мелкие модели (qwen2.5-0.5b/1.5b, llama-3.2-1b).
"""
from __future__ import annotations

import logging
import os
from typing import Optional, List, Dict, Any

import httpx

logger = logging.getLogger(__name__)


class LLMClient:
    """Тонкий клиент к OpenAI-совместимому /v1/chat/completions."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = "not-needed",
        model: Optional[str] = None,
        timeout: float = 120.0,
    ):
        # Базовый URL можно задать переменной окружения (удобно для переключения
        # между LM Studio / llama.cpp / ollama одной строкой).
        self.base_url = (base_url or os.getenv("TGRODER_LLM_URL", "http://localhost:1234")).rstrip("/")
        self.api_key = api_key
        self.model = model or os.getenv("TGRODER_LLM_MODEL")
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 512,
        **kwargs,
    ) -> Optional[str]:
        """Отправить сообщения, вернуть текст ответа или None при ошибке."""
        if not self.model:
            logger.error("LLMClient: модель не задана (TGRODER_LLM_MODEL)")
            return None
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        try:
            resp = self._client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLMClient.chat ошибка: {e}")
            return None

    def analyze_sentiment(self, texts: List[str], images_b64: Optional[List[str]] = None) -> Dict[str, Any]:
        """Извлечь сентимент новостей (текст и опц. фото) в JSON.

        Возвращает {'sentiment': -1..1, 'summary': str, 'symbols': [...]}.
        Модель должна вернуть JSON; если не вернёт — парсим мягко.
        """
        text_block = "\n".join(f"- {t}" for t in texts)
        sys_prompt = (
            "Ты финансовый аналитик крипторынка. Прочитай новости и ответь "
            "ОДНИМ JSON-объектом без пояснений и без markdown:\n"
            '{"verdict": "BUY"|"SELL"|"HOLD", "sentiment": <число -1..1>, '
            '"symbols": ["ТИКЕР"], "why": "<5 слов по-русски>"}\n'
            "verdict BUY если новости позитивны для цены, SELL если негативны, "
            "HOLD если нейтрально. sentiment: -1 медведь, +1 бык."
        )
        # Контент: текст + опц. картинки (vision-модели)
        content: Any = [{"type": "text", "text": f"Новости:\n{text_block}"}]
        if images_b64:
            for img in images_b64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img}"},
                })
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": content},
        ]
        raw = self.chat(messages, temperature=0.1, max_tokens=400)
        return self._parse_sentiment(raw)

    @staticmethod
    def _parse_sentiment(raw: Optional[str]) -> Dict[str, Any]:
        import json
        if not raw:
            return {"sentiment": 0.0, "summary": "нет ответа", "symbols": []}
        parsed = None
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(raw[start:end])
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            # приоритет — явный вердикт модели
            verdict = str(parsed.get("verdict", "")).upper()
            if verdict == "BUY":
                return {"sentiment": 0.8, "summary": parsed.get("why", ""), "symbols": parsed.get("symbols", [])}
            if verdict == "SELL":
                return {"sentiment": -0.8, "summary": parsed.get("why", ""), "symbols": parsed.get("symbols", [])}
            if verdict == "HOLD":
                return {"sentiment": 0.0, "summary": parsed.get("why", ""), "symbols": parsed.get("symbols", [])}
            # иначе берём числовой sentiment, если есть
            if "sentiment" in parsed:
                try:
                    return {"sentiment": float(parsed["sentiment"]),
                             "summary": parsed.get("why", parsed.get("summary", "")),
                             "symbols": parsed.get("symbols", [])}
                except Exception:
                    pass
        # мягкий фолбэк: ищем словесные маркеры
        low = raw.lower()
        s = 0.0
        if any(w in low for w in ["быч", "рост", "buy", "bull", "🚀"]):
            s = 0.5
        elif any(w in low for w in ["медв", "паден", "sell", "bear", "🔻"]):
            s = -0.5
        return {"sentiment": s, "summary": raw[:200], "symbols": []}

    def close(self):
        self._client.close()
