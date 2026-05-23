"""On chain heat indicator.

A 0 to 100 score reflecting how active the $DOG Rune pool is right now. Three
components, each capped at a defensible heuristic threshold:

  1. Fill rate (0 to 40): swaps per minute in the last hour, normalised
     against a busy baseline of 2 swaps per minute.
  2. TVL health (0 to 30): pool TVL in DOG units, normalised against a
     healthy baseline of 100M DOG.
  3. Volume velocity (0 to 30): the ratio of the last hour notional to the
     average hourly notional implied by the 24 hour total. Above 1.0 is
     "hotter than usual"; capped at 3.0 for the full 30 points.

The General agent uses this score to push or hold a directional stance.
"""

from __future__ import annotations

from . import register
from .base import Indicator, IndicatorContext

FILLS_PER_MIN_FULL = 2.0
TVL_FULL_DOG = 100_000_000.0
VELOCITY_FULL = 3.0


def _fill_rate_score(fill_count_1h: int) -> float:
    rate_per_min = fill_count_1h / 60.0
    return min(40.0, (rate_per_min / FILLS_PER_MIN_FULL) * 40.0)


def _tvl_score(tvl_dog: float) -> float:
    if tvl_dog <= 0:
        return 0.0
    return min(30.0, (tvl_dog / TVL_FULL_DOG) * 30.0)


def _velocity_score(recent_fills: list, volume_24h_btc: float) -> float:
    if not recent_fills or volume_24h_btc <= 0:
        return 0.0
    last_hour_btc = sum(float(f.get("notional_btc") or 0.0) for f in recent_fills)
    hourly_avg = volume_24h_btc / 24.0
    if hourly_avg <= 0:
        return 0.0
    ratio = last_hour_btc / hourly_avg
    return min(30.0, (ratio / VELOCITY_FULL) * 30.0)


class OnchainHeatIndicator(Indicator):
    name = "onchain_heat"
    inputs = ["dotswap"]
    window_seconds = 0

    async def compute(self, ctx: IndicatorContext) -> dict:
        now = ctx.now_ts
        ds = await ctx.fetch("dotswap")
        if "error" in ds:
            return {
                "value": None,
                "ts": now,
                "meta": {"stale": True, "sources": ["dotswap"], "notes": ds["error"]},
            }

        fill_rate = _fill_rate_score(int(ds.get("fill_count_1h") or 0))
        tvl = _tvl_score(float(ds.get("tvl_dog") or 0.0))
        velocity = _velocity_score(
            ds.get("recent_fills") or [],
            float(ds.get("volume_24h_btc") or 0.0),
        )

        score = round(fill_rate + tvl + velocity, 1)
        return {
            "value": {
                "score": score,
                "components": {
                    "fill_rate": round(fill_rate, 1),
                    "tvl": round(tvl, 1),
                    "velocity": round(velocity, 1),
                },
                "raw": {
                    "fill_count_1h": int(ds.get("fill_count_1h") or 0),
                    "fill_count_24h": int(ds.get("fill_count_24h") or 0),
                    "tvl_dog": float(ds.get("tvl_dog") or 0.0),
                    "volume_24h_btc": float(ds.get("volume_24h_btc") or 0.0),
                    "floor_sats_per_dog": float(ds.get("floor_sats_per_dog") or 0.0),
                },
            },
            "ts": int(ds.get("ts") or now),
            "meta": {
                "stale": False,
                "sources": ["dotswap"],
                "notes": None,
            },
        }


register(OnchainHeatIndicator())
