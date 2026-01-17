#!/usr/bin/env python3.13
"""
CryptoTgBot - Основной файл запуска приложения
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from config_manager.settings import get_settings
from telegram_bot.bot import CryptoTgBot


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("Запуск CryptoTgBot...")
    
    # Инициализация Telegram бота в фоне
    telegram_bot = CryptoTgBot()
    bot_task = asyncio.create_task(telegram_bot.start())
    
    yield
    
    # Остановка
    logger.info("Остановка CryptoTgBot...")
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass


# Создание FastAPI приложения
app = FastAPI(
    title="CryptoTgBot API",
    description="API для Telegram бота криптовалютной торговли",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "CryptoTgBot API работает!", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "CryptoTgBot"}


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
