"""
Основные роуты API CryptoTeleBot
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .wallet import router as wallet_router
from .trading import router as trading_router
from .auth import get_current_user

router = APIRouter()
security = HTTPBearer()

# Включаем дочерние роутеры
router.include_router(wallet_router, prefix="/wallet", tags=["wallet"])
router.include_router(trading_router, prefix="/trading", tags=["trading"])


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Информация о текущем пользователе"""
    return {
        "user_id": current_user.get("user_id"),
        "username": current_user.get("username"),
        "status": "active"
    }


@router.get("/status")
async def get_system_status():
    """Статус системы"""
    return {
        "status": "operational",
        "services": {
            "database": "connected",
            "redis": "connected", 
            "trading_engine": "ready",
            "telegram_bot": "active"
        },
        "version": "1.0.0"
    }
