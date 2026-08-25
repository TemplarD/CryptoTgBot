"""Smoke-тест движка стратегий TgTrader (без биржи/сети)."""
import asyncio
import sys
import os
import numpy as np

# Добавляем корень backend_python в PYTHONPATH (файл лежит в tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.registry import registry
from trading.strategies import MACrossStrategy, AINewsStrategy  # регистрация
from trading.engine import StrategyEngine
from trading.base import MarketFrame, Action


def make_frame(symbol, closes, balance=100.0, news=None):
    ctx = {"balance_usdt": balance}
    if news:
        ctx["news"] = news
    return MarketFrame(
        symbol=symbol, closes=list(closes),
        timestamps=list(range(len(closes))),
        context=ctx,
    )


async def main():
    print("Зарегистрированные стратегии:", registry.names())
    eng = StrategyEngine(registry, config={
        "min_trade_usdt": 1.0, "max_position_pct": 0.95,
        "commission_rate": 0.001, "commission_buffer": 3.0,
        "take_profit_pct": 0.02, "stop_loss_pct": 0.015, "min_balance_usdt": 1.0,
    })

    # 1) ПАДЕНИЕ -> затем рост (чёткий crossed_up на переломе) -> BUY
    rng = np.random.default_rng(42)
    down = np.linspace(120, 100, 35) + rng.normal(0, 0.3, 35)
    up = np.linspace(100, 125, 35) + rng.normal(0, 0.3, 35)
    series = np.concatenate([down, up])
    sig = await eng.run_cycle(make_frame("BTC/USDT", series, balance=100.0))
    print("\n[Тест 1] Восходящий тренд, баланс $100:")
    print("  ->", sig.action.value if sig else None, "| conf=", round(sig.confidence, 3) if sig else 0,
          "| amount=", round(sig.amount, 3) if sig else 0, "| note=", sig.note if sig else "")

    # 2) МИКРО-депозит $2 — проверяем, что ансамбль работает, размер <= 95%
    sig2 = await eng.run_cycle(make_frame("BTC/USDT", series, balance=2.0))
    print("\n[Тест 2] Восходящий тренд, баланс $2 (микро):")
    if sig2:
        print("  ->", sig2.action.value, "| amount=", round(sig2.amount, 4),
              "(должен быть <= 1.9 = 95% от $2)")
    else:
        print("  -> HOLD/None (ожидалось BUY с amount<=1.9)")

    # 3) KILL-SWITCH: баланс $0.5 < $1 -> торговля на паузе
    sig3 = await eng.run_cycle(make_frame("BTC/USDT", up, balance=0.5))
    print("\n[Тест 3] Kill-switch, баланс $0.5 < $1:")
    print("  ->", sig3.action.value if sig3 else None, "(ожидалось None)")

    # 4) AI NEWS: включаем стратегию и подаём позитивные новости
    registry.enable("ai_news", True)
    print("\n[Тест 4] AI-новости ВКЛ, позитивные новости:")
    news_frame = make_frame("ETH/USDT", list(np.linspace(100, 101, 40)),
                            balance=50.0, news=["Биткоин взлетел, bull breakout 🚀"])
    sig4 = await eng.run_cycle(news_frame)
    print("  ->", sig4.action.value if sig4 else None,
          "| note=", sig4.note if sig4 else "", "| strategy=", sig4.strategy_name if sig4 else "")

    # 5) список для API
    print("\n[Тест 5] /api/strategies список:")
    for s in registry.list_for_api():
        print(f"  - {s['name']:10} enabled={s['enabled']} weight={s['weight']} :: {s['description']}")


if __name__ == "__main__":
    asyncio.run(main())
