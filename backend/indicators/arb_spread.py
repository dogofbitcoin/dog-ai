"""Cross venue arbitrage spread indicator.

Compares the DOG/BTC price on DogSwap (Bitcoin L1 pool via Nexus) against
Kraken (synthetic DOGBTC from `kraken ticker DOGUSD` / `kraken ticker XBTUSD`).
Reports the gap as a percentage and flags when the delta exceeds a threshold.

This is the bridge signal: it shows users on both venues where the opportunity
sits. A positive gap means L1 is cheaper (opportunity for Kraken users to look
at the native pool). A negative gap means Kraken is cheaper (opportunity for L1
users to see exchange demand). Both directions reward transparency.
"""

from __future__ import annotations

import time

from . import register
from .base import Indicator, IndicatorContext

ARB_THRESHOLD_PCT = 2.0


class ArbSpreadIndicator(Indicator):
    name = "arb_spread"
    inputs = ["dotswap", "kraken"]
    window_seconds = 0

    async def compute(self, ctx: IndicatorContext) -> dict:
        ds = await ctx.fetch("dotswap")
        kr = await ctx.fetch("kraken", endpoint="ticker", pair="DOGBTC")

        ds_err = ds.get("error") if isinstance(ds, dict) else "unavailable"
        kr_err = kr.get("error") if isinstance(kr, dict) else "unavailable"

        if ds_err or kr_err:
            notes = []
            if ds_err:
                notes.append(f"dotswap: {ds_err}")
            if kr_err:
                notes.append(f"kraken: {kr_err}")
            return {
                "value": None,
                "ts": int(time.time()),
                "meta": {"stale": True, "sources": ["dotswap", "kraken"], "notes": "; ".join(notes)},
            }

        ds_price_btc = float(ds.get("floor_btc") or 0.0)
        kr_bid = float(kr.get("bid") or 0.0)
        kr_ask = float(kr.get("ask") or 0.0)
        kr_mid = (kr_bid + kr_ask) / 2 if kr_bid and kr_ask else float(kr.get("last") or 0.0)

        if not ds_price_btc or not kr_mid:
            return {
                "value": None,
                "ts": int(time.time()),
                "meta": {"stale": True, "sources": ["dotswap", "kraken"], "notes": "price data missing from one venue"},
            }

        gap_pct = ((kr_mid - ds_price_btc) / ds_price_btc) * 100
        abs_gap = abs(gap_pct)

        if gap_pct > 0:
            direction = "dotswap_cheaper"
            action_hint = "buy on DogSwap L1, sell on Kraken"
        elif gap_pct < 0:
            direction = "kraken_cheaper"
            action_hint = "buy on Kraken, sell on DogSwap L1"
        else:
            direction = "parity"
            action_hint = "no edge"

        actionable = abs_gap >= ARB_THRESHOLD_PCT

        return {
            "value": {
                "gap_pct": round(gap_pct, 3),
                "abs_gap_pct": round(abs_gap, 3),
                "direction": direction,
                "action_hint": action_hint,
                "actionable": actionable,
                "threshold_pct": ARB_THRESHOLD_PCT,
                "dotswap_price_btc": ds_price_btc,
                "dotswap_price_sats": ds_price_btc * 1e8,
                "kraken_bid_btc": kr_bid,
                "kraken_ask_btc": kr_ask,
                "kraken_mid_btc": kr_mid,
                "kraken_mid_sats": kr_mid * 1e8,
                "dotswap_volume_24h_btc": float(ds.get("volume_24h_btc") or 0.0),
                "dotswap_fill_count_24h": int(ds.get("fill_count_24h") or 0),
                "dotswap_tvl_dog": float(ds.get("tvl_dog") or 0.0),
            },
            "ts": int(time.time()),
            "meta": {
                "stale": False,
                "sources": ["dotswap", "kraken"],
                "notes": None,
            },
        }


register(ArbSpreadIndicator())
