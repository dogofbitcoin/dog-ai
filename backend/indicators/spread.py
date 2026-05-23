"""Spread indicator.

Top of book bid/ask spread on the configured Kraken pair. Returns the spread in
basis points plus the raw quotes. Snapshot indicator; no window.
"""

from __future__ import annotations

import time

from . import register
from .base import Indicator, IndicatorContext


class SpreadIndicator(Indicator):
    name = "spread"
    inputs = ["kraken"]
    window_seconds = 0

    async def compute(self, ctx: IndicatorContext) -> dict:
        tk = await ctx.fetch("kraken", endpoint="ticker")
        if "error" in tk:
            return {
                "value": None,
                "ts": int(time.time()),
                "meta": {"stale": True, "sources": ["kraken"], "notes": tk["error"]},
            }
        bid = float(tk.get("bid") or 0.0)
        ask = float(tk.get("ask") or 0.0)
        mid = (bid + ask) / 2 if bid and ask else 0.0
        bps = ((ask - bid) / mid) * 10_000 if mid else 0.0
        return {
            "value": {
                "pair": tk.get("pair"),
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "spread_bps": round(bps, 2),
                "synthetic": tk.get("synthetic", False),
            },
            "ts": int(tk.get("ts") or time.time()),
            "meta": {
                "stale": False,
                "sources": ["kraken"],
                "notes": None,
            },
        }


register(SpreadIndicator())
