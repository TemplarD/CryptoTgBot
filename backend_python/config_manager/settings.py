"""
Настройки приложения CryptoTeleBot
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Приложение
    app_name: str = "CryptoTeleBot"
    debug: bool = False
    version: str = "1.0.0"
    
    # Telegram
    telegram_api_id: int
    telegram_api_hash: str
    telegram_bot_token: str
    
    # База данных
    database_url: str = "postgresql://botuser:password@localhost/cryptobot"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Безопасность
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Торговля
    default_exchange: str = "binance"
    max_position_size: float = 100.0
    risk_percentage: float = 2.0
    
    # Анализ
    pattern_window_size: int = 100
    similarity_threshold: float = 0.85
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Получение настроек (с кэшированием)"""
    return Settings()
