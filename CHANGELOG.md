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

### ⏭️ Дальше:
- Реализовать `CCXTExecutor` (реальная биржа по API-ключам)
- Подключить `NewsAnalyzer` к локальному ollama (чтение фото новостей)
- Pattern-стратегия поверх Rust-ядра `find_similar_patterns`
- Mini App: переключатель стратегий, баланс, графики
