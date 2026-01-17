# CryptoTgBot - Гибридный автоматический торговый бот

🤖 **Интеллектуальный Telegram бот для автоматической криптовалютной торговли с анализом исторических паттернов**

## 📋 Обзор проекта

**CryptoTgBot** - это гибридная система, объединяющая:
- **Python** для управления и API
- **Rust** для высокопроизводительного анализа данных
- **Telegram Mini App** для удобного интерфейса

**Основная цель:** Автоматическая торговля криптовалютами с использованием машинного обучения для анализа паттернов.

## 🏗️ Архитектура

```
cryptotgbot/
├── frontend/                    # Telegram Mini App (JavaScript)
│   ├── dashboard.html          # Основной интерфейс
│   ├── wallet.html            # Управление кошельком
│   ├── styles.css             # Стили
│   └── app.js                 # Логика приложения
├── backend_python/            # Python слой управления
│   ├── main.py               # Точка входа FastAPI
│   ├── telegram_bot/         # Работа с Telegram API
│   ├── api/                  # REST API endpoints
│   ├── config_manager/       # Управление конфигурацией
│   ├── data/                 # Работа с данными
│   └── trading/              # Торговая логика
├── backend_rust/             # Rust слой ядра
│   ├── Cargo.toml           # Конфигурация Rust
│   ├── src/lib.rs           # Основная библиотека
│   ├── src/analysis/        # Анализ данных
│   └── src/trading/         # Исполнение сделок
├── data/                    # Исторические данные
│   ├── historical/          # Сырые данные
│   └── processed/           # Обработанные данные
└── docker/                  # Контейнеризация
```

## 🛠️ Технологический стек

### Backend Python (управление):
- **Python 3.13+** - основной язык
- **FastAPI 0.115+** - REST API сервер
- **SQLAlchemy 2.0+** - ORM для базы данных
- **PostgreSQL 18+** - основная база данных
- **Redis** - кэширование и очередь сообщений
- **Telethon** - работа с Telegram API
- **AIOHTTP** - асинхронные HTTP запросы

### Backend Rust (ядро):
- **Rust 1.85+** - системный язык
- **Tokio** - асинхронный runtime
- **PyO3** - Python биндинги
- **Rayon** - параллельные вычисления
- **NDArray** - численные вычисления
- **TON SDK** - работа с блокчейном TON

### Frontend (Telegram Mini App):
- **HTML5/CSS3/JavaScript ES6+**
- **Chart.js** - графики и визуализация
- **Telegram WebApp API** - интеграция с Telegram
- **TON Connect 2** - подключение кошельков TON

### Инфраструктура:
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - reverse proxy
- **Ubuntu 24.04 LTS** - основная ОС

## 🚀 Быстрый старт

### Требования:
- Docker & Docker Compose
- Python 3.13+
- Rust 1.85+
- PostgreSQL 18+
- Redis

### Установка:

1. **Клонирование репозитория:**
```bash
git clone https://github.com/TemplarD/CryptoTgBot.git
cd CryptoTgBot
```

2. **Настройка окружения:**
```bash
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

3. **Запуск через Docker Compose:**
```bash
docker-compose up -d
```

4. **Локальная разработка:**
```bash
# Backend Python
cd backend_python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Backend Rust
cd backend_rust
cargo build --release
```

## 📱 Использование

### Telegram Bot:
1. Найдите бота в Telegram
2. Нажмите `/start`
3. Откройте Mini App для доступа к полному функционалу

### Mini App Функции:
- 📊 **Дашборд** - обзор портфеля и баланса
- 💰 **Кошелек** - управление TON кошельком
- 📈 **Торговля** - автоматическая торговля
- 🎯 **Сигналы** - торговые сигналы на основе анализа
- 📉 **Графики** - визуализация данных

## 🔧 Конфигурация

Основные настройки в `.env` файле:

```env
# Telegram Bot API
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# База данных
DATABASE_URL=postgresql://botuser:password@localhost:5432/cryptobot

# Redis
REDIS_URL=redis://localhost:6379/0

# Безопасность
SECRET_KEY=your_very_secure_secret_key
```

## 🌐 Ветки разработки

- **master** - основная ветка для продакшена
- **develop** - ветка для разработки (текущая)
- **test** - ветка для тестирования

## 📊 Текущий статус

### ✅ Этап 0: Завершен
- [x] Базовая структура проекта
- [x] Настройка окружения разработки
- [x] Docker конфигурация
- [x] Базовый API и фронтенд

### 🔄 Этап 1: В разработке
- [ ] Минимальный работающий продукт
- [ ] Telegram Mini App с данными кошелька
- [ ] Базовая интеграция с TON

### 📋 Планируемые этапы:
- **Этап 2:** Rust ядро для анализа паттернов
- **Этап 3:** Сбор исторических данных
- **Этап 4:** Система автоматической торговли

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature ветку (`git checkout -b feature/AmazingFeature`)
3. Commit ваши изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл LICENSE для деталей.

## 📞 Контакты

- **GitHub:** [TemplarD](https://github.com/TemplarD)
- **Проект:** [CryptoTgBot](https://github.com/TemplarD/CryptoTgBot)

---

⚡ **Начните с `git checkout develop` для разработки!**
