"""Smoke-тест реального LLM (llama.cpp server :8080) через LLMClient + ai_news."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.registry import registry
from trading.llm import LLMClient
from trading.engine import StrategyEngine
from trading.base import MarketFrame

# Указываем на поднятый llama-server
os.environ["TGRODER_LLM_URL"] = "http://127.0.0.1:8080"
os.environ["TGRODER_LLM_MODEL"] = "qwen2.5-0.5b-instruct-q4_k_m.gguf"

import numpy as np

async def main():
    print("=== прямой вызов LLMClient (сентимент) ===")
    llm = LLMClient()
    r = llm.analyze_sentiment([
        "Bitcoin резко вырос на 12% после одобрения ETF, аналитики ждут продолжения бычьего тренда!"
    ])
    print("  позитив:", r)
    r2 = llm.analyze_sentiment([
        "Рынок обвалился, BTC упал на 20%, паника среди инвесторов, медвежий тренд."
    ])
    print("  негатив:", r2)

    print("\n=== интеграция в движок (ai_news ВКЛ) ===")
    registry.enable("ai_news", True)
    eng = StrategyEngine(registry, config={
        "min_trade_usdt": 1.0, "max_position_pct": 0.95,
        "commission_rate": 0.001, "commission_buffer": 3.0,
        "take_profit_pct": 0.02, "stop_loss_pct": 0.015, "min_balance_usdt": 1.0,
    })
    fr = MarketFrame(symbol="BTC/USDT", closes=list(np.linspace(100, 105, 40)),
                     timestamps=list(range(40)),
                     context={"balance_usdt": 50.0, "news": [
                         "Bitcoin взлетает, крупные покупки институционалов, бычий сигнал!"
                     ]})
    sig = await eng.run_cycle(fr, balance_usdt=50.0)
    print("  сигнал:", sig)
    if sig:
        print("  ->", sig.action.value, "conf", round(sig.confidence,2), "amount", round(sig.amount,2), "note:", sig.note)

asyncio.run(main())
