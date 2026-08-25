"""Отладка ma_cross: печатает внутренности индикаторов."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import asyncio
from trading.strategies.ma_cross import MACrossStrategy, _sma, _rsi
from trading.base import MarketFrame

rng = np.random.default_rng(42)
down = np.linspace(120, 100, 35) + rng.normal(0, 0.3, 35)
up = np.linspace(100, 125, 35) + rng.normal(0, 0.3, 35)
s = np.concatenate([down, up]).tolist()

print("len", len(s), "close[-1]", round(s[-1], 2))
print("fast_now", round(_sma(s, 9), 2), "slow_now", round(_sma(s, 21), 2))
print("fast_prev", round(_sma(s[:-1], 9), 2), "slow_prev", round(_sma(s[:-1], 21), 2))
print("rsi", round(_rsi(s, 14), 2))

st = MACrossStrategy()
fr = MarketFrame(symbol="X", closes=s, timestamps=list(range(len(s))),
                 context={"balance_usdt": 100})
sig = asyncio.run(st.analyze(fr))
print("signal:", sig)
if sig:
    print("  action", sig.action.value, "amount", round(sig.amount, 3), "note", sig.note)
