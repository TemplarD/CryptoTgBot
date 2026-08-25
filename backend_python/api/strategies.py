"""
API управления стратегиями.

Позволяет из Telegram-бота / Mini App:
  GET  /api/strategies            — список всех стратегий + статус
  POST /api/strategies/{name}/enable   — вкл/выкл (body: {"enabled": true})
  POST /api/strategies/{name}/weight    — задать вес (body: {"weight": 1.5})

Движок и реестр создаются в main.py и кладутся в app.state.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from trading.registry import registry

router = APIRouter(tags=["strategies"])


class EnableBody(BaseModel):
    enabled: bool


class WeightBody(BaseModel):
    weight: float


@router.get("/strategies")
async def list_strategies():
    return {"strategies": registry.list_for_api()}


@router.post("/strategies/{name}/enable")
async def set_enabled(name: str, body: EnableBody):
    if not registry.enable(name, body.enabled):
        raise HTTPException(404, f"Стратегия '{name}' не найдена")
    return {"name": name, "enabled": body.enabled}


@router.post("/strategies/{name}/weight")
async def set_weight(name: str, body: WeightBody):
    if not registry.set_weight(name, body.weight):
        raise HTTPException(404, f"Стратегия '{name}' не найдена")
    return {"name": name, "weight": body.weight}
