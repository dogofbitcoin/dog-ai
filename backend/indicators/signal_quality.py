"""Signal quality indicator.

A 0 to 100 composite score combining three things:

  1. Freshness (0 to 40): how recent are the kraken and dotswap snapshots.
     Both within 30 seconds scores the full 40 and decays linearly to 0 at
     5 minutes.
  2. Depth (0 to 30): Kraken top of book has tradeable size on both sides.
     A simple threshold model in v0.1.
  3. Agreement (0 to 30): how close DotSwap floor is to the Kraken bid in
     BTC terms. Within 1% scores 30, 5% scores 15, 10% or more scores 0.

The Alpha agent uses this score to gate confidence in its stance.
"""

from __future__ import annotations

from . import register
from .base import Indicator, IndicatorContext

FRESH_FULL_S = 30
FRESH_ZERO_S = 300

DEPTH_FULL_USD = 250.0  # USD notional on each side considered "full"


def _freshness_score(age_seconds: float) -> float:
    if age_seconds <= FRESH_FULL_S:
        return 40.0
    if age_seconds >= FRESH_ZERO_S:
        return 0.0
    # Linear decay from 40 to 0 across the band.
    span = FRESH_ZERO_S - FRESH_FULL_S
    return 40.0 * (1.0 - (age_seconds - FRESH_FULL_S) / span)


def _depth_score(orderbook: dict) -> float:
    if not orderbook or "error" in orderbook:
        return 0.0
    bids = orderbook.get("bids") or []
    asks = orderbook.get("asks") or []
    bid_notional = sum(p * v for p, v in bids[:3])
    ask_notional = sum(p * v for p, v in asks[:3])
    side = min(bid_notional, ask_notional)
    if side >= DEPTH_FULL_USD:
        return 30.0
    if side <= 0:
        return 0.0
    return 30.0 * (side / DEPTH_FULL_USD)


def _agreement_score(kraken_bid: float, dotswap_floor: float) -> float:
    if not kraken_bid or not dotswap_floor:
        return 0.0
    diff = abs(kraken_bid - dotswap_floor) / max(kraken_bid, dotswap_floor)
    if diff <= 0.01:
        return 30.0
    if diff >= 0.10:
        return 0.0
    # Linear between 1% and 10%
    return 30.0 * (1.0 - (diff - 0.01) / 0.09)


class SignalQualityIndicator(Indicator):
    name = "signal_quality"
    inputs = ["kraken", "dotswap"]
    window_seconds = 0

    async def compute(self, ctx: IndicatorContext) -> dict:
        now = ctx.now_ts
        kr_ticker = await ctx.fetch("kraken", endpoint="ticker")
        kr_book = await ctx.fetch("kraken", endpoint="orderbook", count=10)
        ds = await ctx.fetch("dotswap")

        notes_parts: list[str] = []
        if "error" in kr_ticker:
            notes_parts.append(f"kraken ticker: {kr_ticker['error']}")
        if "error" in kr_book:
            notes_parts.append(f"kraken book: {kr_book['error']}")
        if "error" in ds:
            notes_parts.append(f"dotswap: {ds['error']}")

        kr_ts = int(kr_ticker.get("ts") or 0) if "error" not in kr_ticker else 0
        ds_ts = int(ds.get("ts") or 0) if "error" not in ds else 0
        oldest_ts = min(t for t in (kr_ts, ds_ts) if t) if (kr_ts and ds_ts) else 0
        age = (now - oldest_ts) if oldest_ts else FRESH_ZERO_S

        freshness = _freshness_score(age)
        depth = _depth_score(kr_book)
        agreement = _agreement_score(
            kraken_bid=float(kr_ticker.get("bid") or 0.0) if "error" not in kr_ticker else 0.0,
            dotswap_floor=float(ds.get("floor_btc") or 0.0) if "error" not in ds else 0.0,
        )

        score = round(freshness + depth + agreement, 1)
        stale = bool(notes_parts) or age >= FRESH_ZERO_S

        return {
            "value": {
                "score": score,
                "components": {
                    "freshness": round(freshness, 1),
                    "depth": round(depth, 1),
                    "agreement": round(agreement, 1),
                },
                "age_seconds": int(age),
            },
            "ts": now,
            "meta": {
                "stale": stale,
                "sources": ["kraken", "dotswap"],
                "notes": "; ".join(notes_parts) if notes_parts else None,
            },
        }


register(SignalQualityIndicator())
