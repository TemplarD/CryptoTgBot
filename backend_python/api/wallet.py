"""
API для работы с кошельками
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class WalletInfo(BaseModel):
    """Модель информации о кошельке"""
    address: str
    balance: float
    usd_value: float
    transactions: List[Dict[str, Any]]


class Transaction(BaseModel):
    """Модель транзакции"""
    hash: str
    type: str  # 'in' или 'out'
    amount: float
    timestamp: str
    from_address: str = None
    to_address: str = None


@router.get("/info", response_model=WalletInfo)
async def get_wallet_info():
    """
    Получение информации о кошельке пользователя
    
    TODO: Реализовать получение данных из TON blockchain
    """
    # Временные mock данные
    mock_wallet = WalletInfo(
        address="EQD...example_address",
        balance=125.5,
        usd_value=627.5,  # при курсе $5/TON
        transactions=[
            {
                "hash": "tx_123...",
                "type": "in",
                "amount": 50.0,
                "timestamp": "2025-01-07T10:30:00Z",
                "from_address": "EQA...sender"
            },
            {
                "hash": "tx_456...",
                "type": "out", 
                "amount": 25.0,
                "timestamp": "2025-01-07T09:15:00Z",
                "to_address": "EQB...recipient"
            }
        ]
    )
    
    return mock_wallet


@router.get("/balance")
async def get_wallet_balance():
    """Получение баланса кошелька"""
    # TODO: Реализовать получение реального баланса
    return {
        "ton": 125.5,
        "usd_value": 627.5,
        "last_updated": "2025-01-07T12:00:00Z"
    }


@router.get("/transactions", response_model=List[Transaction])
async def get_wallet_transactions(limit: int = 50, offset: int = 0):
    """
    Получение истории транзакций
    
    Args:
        limit: Количество транзакций
        offset: Смещение для пагинации
    """
    # TODO: Реализовать получение реальных транзакций
    mock_transactions = [
        Transaction(
            hash="tx_123...",
            type="in",
            amount=50.0,
            timestamp="2025-01-07T10:30:00Z",
            from_address="EQA...sender"
        ),
        Transaction(
            hash="tx_456...",
            type="out",
            amount=25.0,
            timestamp="2025-01-07T09:15:00Z",
            to_address="EQB...recipient"
        )
    ]
    
    return mock_transactions[offset:offset + limit]


@router.post("/connect")
async def connect_wallet(wallet_address: str):
    """
    Подключение кошелька к аккаунту
    
    Args:
        wallet_address: Адрес TON кошелька
    """
    # TODO: Реализовать проверку и сохранение адреса кошелька
    return {
        "status": "success",
        "message": "Кошелек успешно подключен",
        "address": wallet_address
    }
