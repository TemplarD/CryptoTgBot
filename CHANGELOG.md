# Журнал разработки TgTrader (CryptoTgBot)

## 🐱 2026-08-25 - Движок стратегий + починка Rust-ядра

### ✅ Сделано:
1. **Плагин-архитектура стратегий** (`backend_python/trading/`):
   - `base.py` — единый контракт `TradeSignal` / `MarketFrame` / `Strategy`
   - `registry.py` — реестр (включать/выключать/вес стратегий из ТГ/Mini App)
   - `engine.py` — **ансамбль** (взвешенное голосование стратегий = решение по
     совокупности данных) + **жёсткий учёт комиссий** + **kill-switch для
     микро-депозита** (торговля на паузе при балансе < $1)
2. **Рабочие стратегии**:
   - `ma_cross.py` — базовая (MA cross + RSI, трендовая)
   - `ai_news.py` — **заготовка под нейросеть** (интерфейс `NewsAnalyzer`,
     готовый под локальный ollama для чтения новостей/фото и сентимента)
3. **PaperExecutor** (`executor.py`) — симулятор сделок с комиссиями
   (песочница для проверки стратегий без реальных денег)
4. **API управления стратегиями** (`api/strategies.py`):
   - `GET /api/strategies` — список + статус
   - `POST /api/strategies/{name}/enable` — вкл/выкл
   - `POST /api/strategies/{name}/weight` — вес для ансамбля
   Подключено в `routes.py` и инициализировано в `main.py` (lifespan).
5. **Rust-ядро починено**:
   - убраны несуществующие зависимости `ton-labs-*` (ломали сборку)
   - `lib.rs` переписан под PyO3 0.22 API (`Bound`, `PyArrayMethods`,
     `empty_bound`)
   - добавлен недостающий `src/analysis/mod.rs` с `PatternMatcher`
   - `cargo build` проходит ✅ (`libcrypto_core.so` собран)
6. **Smoke-тест** `tests/smoke_strategies.py` — 5 проверок (тренд→BUY,
   микро-$2→BUY с лимитом, kill-switch, AI-новости→BUY, список API).

### 📌 Важно про архитектуру (сверка с реальным Telegram):
- Родной **@wallet** в ТГ — кастодиальный, у бота НЕТ API исполнять сделки
  оттуда. Авто-трейдинг биржевых пар через него невозможен.
- Реальный путь для идеи (микро-$2, комиссии, стратегии, новости) —
  **биржевая торговля через ccxt** по API-ключам пользователя
  (Binance/Bybit). `ccxt` уже в requirements. TON DEX (через TON Connect из
  Mini App) — опционально позже.
- План: `CCXTExecutor` (приоритет) + `PaperExecutor` (готов) + позже
  `TonConnectExecutor`. UI/управление — бот + Mini App (+ Telegram Stars для
  платных ИИ-стратегий в перспективе).

### ⚠️ УТОЧНЕНИЕ по Telegram Wallet (найдено через поиск, 2025-2026):
Ранее считалось, что @Wallet (родной ТГ-кошелёк) — только кастодиальное
хранилище без торговли. **Это устарело.** Актуальное состояние:
- **Wallet in Telegram** (от The Open Platform, custodial) теперь даёт
  **perpetual futures (перпы) через интеграцию с Lighter**: до **50x плеча**,
  **минимальная позиция $1**, 50+ рынков (BTC, TON, ETH, токенизированные
  акции/комодити), TP/SL, P&L — **не выходя из ТГ**.
- Есть **Earn/yield** (TON, позже USDT), спот-свопы, P2P, стейкинг.
- ❗ НО программного bot-API для *авто*-исполнения этих сделок от имени
  бота пока не найдено (интерфейс — Mini App, пользователь нажимает сам).
  Нужно докопать partner/TON Connect API. Пока рабочий путь автоторговли —
  всё ещё **ccxt + API-ключи биржи** (Binance/Bybit Futures). @Wallet-перпы —
  кандидат на `TonConnectExecutor`/Mini App-интеграцию позже.

## 🐱 2026-08-25 (доп) - LLM напрямую (llama.cpp / LM Studio)

### ✅ Сделано:
1. `trading/llm.py` — **универсальный LLM-клиент** к OpenAI-совместимому
   `/v1/chat/completions`. Работает с ЛЮБЫМ бэкендом одной строкой конфига:
   - LM Studio (`http://localhost:1234`, внутри — llama.cpp server)
   - чистый llama.cpp (`./llama-server -m model.gguf --port 8080`)
   - ollama (`http://localhost:11434`)
   Переключение через `TGRODER_LLM_URL` / `TGRODER_LLM_MODEL`.
2. `trading/strategies/ai_news.py` переписан на реальный вызов `LLMClient`
   (с фолбэком-эвристикой, если LLM недоступен). Поддержка **VISION**
   (чтение фото новостей) заложена в `analyze_sentiment`.
3. Найдена и **докачана мелкая модель** `Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`
   (~105MB) в `/home/templard/.lmstudio/models/` для быстрых CPU-тестов
   (железо: 2× Xeon E5-2666v3, 128GB RAM, слабая GPU -> инференс на CPU).

### 💡 Почему llama.cpp напрямую, а не только ollama:
- тонкая настройка (temperature, top_p, repeat_penalty, chat-template)
- VISION-модели (llama3.2-vision и т.п.) — "чтение фото новостей нейронкой"
- любые GGUF, параллельные слоты, контроль KV-cache
- LM Studio у пользователя уже есть (`/home/templard/.lmstudio/bin/lms`) и
  поднимает llama.cpp-сервер на :1234 (`lms server start`).

### ⏭️ Дальше:
- Дособрать `llama-server` (форк furyx) и проверить реальный вызов сентимента
- Реализовать `CCXTExecutor` (реальная биржа/фьючерсы по API-ключам)
- Pattern-стратегия поверх Rust-ядра `find_similar_patterns`
- Mini App: переключатель стратегий, баланс, графики
