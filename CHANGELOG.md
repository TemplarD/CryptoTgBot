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
- Pattern-стратегия поверх Rust-ядра `find_similar_patterns`
- Mini App: переключатель стратегий, баланс, графики

## 🐱 2026-08-25 (доп2) - Варианты программного управления кошельком + CCXTExecutor

### 🔍 Найдено поиском (варианты управления кошельком программно):
1. **TON Connect 2** (`@tonconnect/sdk`, `@tonconnect/ui-react`, `WalletKit`):
   стандарт подключения non-custodial TON-кошелька (Tonkeeper, MyTonWallet,
   **Wallet in Telegram**, Bitget, OKX) к Mini App. Поток: юзер жмёт Connect →
   дApp получает адрес → `sendTransaction({messages})`. **Подпись делает САМ
   ПОЛЬЗОВАТЕЛЬ** в кошельке (human-readable). Бот не держит ключи.
   => полу-автомат: сигнал бота → юзер подтверждает в 1 тап. Только спот DEX.
2. **Blum** (Telegram Mini App): perps до 100x, спот, 20+ активов, не-custodial,
   мультичейн. НО **закрытый Mini App, нет публичного API** для внешнего бота.
   Показывает, что "фьючерсы в ТГ" реальны, но не как платформа для нас.
3. **ccxt + API-ключи биржи** (Binance/Bybit): единственный путь **полной
   автономной** автоторговли (без подтверждения юзером). Ключи trade-only.

### 📌 Итоговая матрица (что выбираем в архитектуре):
| Способ | Автономность | Фьючерсы | Микро-$2 | Программный API |
|--------|------------|---------|---------|----------------|
| ccxt + ключи биржи | ✅ полная | ✅ | ✅ | ✅ REST |
| TON Connect + Mini App | ⚠️ тап юзера | ❌ спот DEX | ⚠️ газ TON | ⚠️ инициация+подтверждение |
| @Wallet перпы (Lighter) | ❌ только UI | ✅ | ✅ $1 | ❌ нет публичного API |
| Blum | ❌ только UI | ✅ | ✅ | ❌ закрытый |

=> `CCXTExecutor` (приоритет, полная автономия) + позже `TonConnectExecutor`
(полу-автомат для TON-юзеров).

### ✅ Сделано:
- `trading/executor.py`: добавлен **`CCXTExecutor`** (реальная торговля через
  ccxt: спот/фьючерсы, ленивый импорт ccxt, sandbox/testnet по умолчанию,
  учёт комиссии из ответа биржи). Рядом `PaperExecutor` (песочница).
- `trading/engine.py`: метод `make_executor(kind)` — фабрика исполнителей
  (`paper` / `ccxt`), готовая точка расширения под `tonconnect`.
- Примечание: ccxt не установлен в venv (только в requirements) — импорт
  ленивый, проект запускается без него; для реальной торговли нужен `pip install ccxt`.

### ⏭️ Дальше:
- Pattern-стратегия поверх Rust-ядра `find_similar_patterns`
- `TonConnectExecutor` (полу-автомат через Mini App)
- Mini App: переключатель стратегий/исполнителей, баланс, графики
- Подключить `CCXTExecutor` к эндпоинту `/api/trading/execute` (с безопасной
  передачей API-ключей пользователя)
