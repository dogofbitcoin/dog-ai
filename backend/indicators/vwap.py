"""VWAP indicator.

Rolling volume weighted average price over `VWAP_WINDOW_SECONDS` (default 300).
The buffer is process local. On restart the window refills over time; this is
deliberate for v0.1 and noted in the CHANGELOG as a v0.2 candidate.
"""

from __future__ import annotations

import os
import time
from collections import deque

from . import register
from .base import Indicator, IndicatorContext


class VwapIndicator(Indicator):
    name = "vwap"
    inputs = ["kraken"]

    def __init__(self) -> None:
        self.window_seconds = int(os.getenv("VWAP_WINDOW_SECONDS", "300"))
        # Each entry: (ts, price, volume)
        self._buf: deque[tuple[int, float, float]] = deque(maxlen=10_000)

    async def compute(self, ctx: IndicatorContext) -> dict:
        trades_payload = await ctx.fetch("kraken", endpoint="trades", count=50)
        now = ctx.now_ts
        if "error" in trades_payload:
            return {
                "value": None,
                "ts": now,
                "meta": {"stale": True, "sources": ["kraken"], "notes": trades_payload["error"]},
            }

        for t in trades_payload.get("trades", []):
            ts = int(t.get("ts") or 0)
            price = float(t.get("price") or 0.0)
            volume = float(t.get("volume") or 0.0)
            if ts and price and volume:
                self._buf.append((ts, price, volume))

        cutoff = now - self.window_seconds
        while self._buf and self._buf[0][0] < cutoff:
            self._buf.popleft()

        if not self._buf:
            return {
                "value": None,
                "ts": now,
                "meta": {
                    "stale": True,
                    "sources": ["kraken"],
                    "notes": "no trades in window yet",
                },
            }

        notional = sum(p * v for _, p, v in self._buf)
        size = sum(v for _, _, v in self._buf)
        vwap = notional / size if size else 0.0

        return {
            "value": {
                "vwap": vwap,
                "window_seconds": self.window_seconds,
                "samples": len(self._buf),
                "pair": trades_payload.get("pair"),
                "synthetic": trades_payload.get("synthetic", False),
            },
            "ts": now,
            "meta": {
                "stale": False,
                "sources": ["kraken"],
                "notes": None,
            },
        }


register(VwapIndicator())
