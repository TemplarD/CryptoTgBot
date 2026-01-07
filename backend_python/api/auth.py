"""
Аутентификация и авторизация для API
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config_manager.settings import get_settings

settings = get_settings()
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Dict:
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительные учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получение текущего пользователя из токена"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительные учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Реализовать получение данных пользователя из БД
    user = {
        "user_id": user_id,
        "username": payload.get("username"),
        "is_active": True
    }
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def authenticate_telegram_user(init_data: str) -> Dict:
    """
    Аутентификация пользователя через Telegram WebApp initData
    
    TODO: Реализовать проверку подписи Telegram
    """
    # Временная реализация - в продакшене нужна проверка подписи
    mock_user = {
        "user_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "is_active": True
    }
    
    return mock_user


def create_user_token(user_data: Dict) -> str:
    """Создание токена для пользователя"""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user_data["user_id"], "username": user_data.get("username")},
        expires_delta=access_token_expires
    )
    return access_token
