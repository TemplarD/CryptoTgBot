# Где брать ключи и что регистрировать (TgTrader / CryptoTgBot)

Короткий гид: какие доступы нужны боту, где их получить, и что именно
регистрировать в Telegram / на бирже. Всё кладётся в `.env` (копия из
`.env.example`), НИКОГДА не в код и не в git.

---

## 1. Telegram Bot (обязательно)

### Что регистрировать
- **Бот** у @BotFather — даёт `TELEGRAM_BOT_TOKEN`.
- **Приложение** на https://my.telegram.org (API development tools) — даёт
  `TELEGRAM_API_ID` + `TELEGRAM_API_HASH` (нужны Telethon-клиенту бота).
- **Mini App** у @BotFather (команда `/newapp` или через BotFather -> Bot ->
  Mini App) — привязывает URL дашборда (`TELEGRAM_WEBAPP_URL`).

### Где брать
| Переменная | Где |
|---|---|
| `TELEGRAM_BOT_TOKEN` | @BotFather → /newbot → токен вида `123456:ABC-DEF` |
| `TELEGRAM_API_ID` | https://my.telegram.org → API development tools → App api_id |
| `TELEGRAM_API_HASH` | там же → App api_hash |
| `TELEGRAM_BOT_USERNAME` | имя бота без @ (из /newbot) |
| `TELEGRAM_WEBAPP_URL` | URL твоего задеплоенного Mini App (ngrok/Domain) |

---

## 2. Биржа (CCXT) — для автоторговли

### Что регистрировать
API-ключ биржи с правами **ТОЛЬКО на торговлю**.

### Где брать (пример — Binance)
1. https://www.binance.com/en/my/settings/api-management
2. Create API Key → выбрать "Spot & Margin Trading" (или Futures)
3. **НЕ ставить галочку Enable Withdrawals** (критично!)
4. Скопировать API Key + Secret
5. Включить IP-allowlist — только IP твоего сервера (безопасность)

Для **Bybit / OKX / других** — аналогично в их разделе API.

### Testnet (рекомендую для разработки — без реальных денег)
- Binance Futures testnet: https://testnet.binancefuture.com/
- Bybit testnet: https://testnet.bybit.com/
- Создаёшь отдельный ключ в testnet, ставишь `EXCHANGE_TESTNET=true`.

| Переменная | Значение |
|---|---|
| `EXCHANGE_ID` | `binance` / `bybit` / `okx` |
| `EXCHANGE_API_KEY` | из личного кабинета биржи |
| `EXCHANGE_SECRET` | из личного кабинета биржи |
| `EXCHANGE_MARKET_TYPE` | `spot` или `future` |
| `EXCHANGE_TESTNET` | `true` (песочница) / `false` (реал) |

> Бот использует ключ только для создания ордеров (CCXTExecutor).
> Права на вывод отключены → бот физически не может увести средства.

---

## 3. LLM (локальный llama.cpp) — для стратегии ai_news

### Что нужно
- Собранный `llama-server` (уже есть: `/home/templard/llama.cpp-furyx/build/bin/llama-server`)
- Модель GGUF (уже есть: `qwen2.5-0.5b-instruct-q4_k_m.gguf`, ~469MB)
- Запуск на всех ядрах CPU (на твоём сервере 40 потоков):

```bash
cd /home/templard/llama.cpp-furyx && ./build/bin/llama-server \
  -m /home/templard/.lmstudio/models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  --port 8080 --host 127.0.0.1 -c 4096 -t 40 -tb 40
```

| Переменная | Значение |
|---|---|
| `TGRODER_LLM_URL` | `http://localhost:8080` (llama.cpp) / `:1234` (LM Studio) / `:11434` (ollama) |
| `TGRODER_LLM_MODEL` | имя GGUF-файла модели |

> Модель до ~2GB идёт быстро на 40 потоках CPU. Большие — очень медленно,
> не качаем. Мелкие (до 2GB) можно пробовать и мерить скорость (tokens/s).

---

## 4. База данных / Redis (уже в docker-compose)
- PostgreSQL 18 + Redis 7 поднимаются через `docker-compose.yml`.
- `DB_PASSWORD`, `REDIS_PASSWORD` — придумай сам, укажи в `.env`.
- `SECRET_KEY` — `openssl rand -hex 32`.

---

## 5. TON Connect (опционально, позже — для TON-пути)
- Нужен **manifest** `tonconnect-manifest.json`, размещённый на твоём домене
  (URL указывается в Mini App).
- Подключает non-custodial TON-кошелёк юзера; подпись делает САМ юзер (тап).
- НЕ требует приватных ключей. Безопасно по дизайну.

---

## Итого: минимум для запуска автоторговли
1. `TELEGRAM_BOT_TOKEN` + `TELEGRAM_API_ID/HASH` (от @BotFather и my.telegram.org)
2. `EXCHANGE_API_KEY/SECRET` с правами trade-only (от биржи, testnet для старта)
3. Локальный `llama-server` запущен (для ai_news; можно и без него — стратегия
   упадёт в эвристику-фолбэк)
4. PostgreSQL + Redis (через docker-compose)
