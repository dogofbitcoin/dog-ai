"""General agent.

Reads `onchain_heat` and `spread`. Produces a directional stance on the rune.

Heat is the primary driver. Spread acts as a guard: even if heat is high, a
wide spread (thin liquidity) tempers the stance. The General does not look at
price levels or VWAP; that is intentional. It speaks to "are buyers showing up
right now," not "is this a good entry."

Stances:
  bullish   heat is hot and the market is tradeable
  neutral   middling heat, or hot heat but the book is thin
  bearish   heat is cold or fading

If `ANTHROPIC_API_KEY` is set, the reasoning string can optionally be rewritten
by an LLM call via `narrate.maybe_narrate`. The stance stays rule based.
"""

from __future__ import annotations

import time

from . import register
from .base import Agent, AgentContext
from .narrate import maybe_narrate

HEAT_HOT = 65.0
HEAT_COLD = 35.0
WIDE_SPREAD_BPS = 80.0


class GeneralAgent(Agent):
    name = "general"
    inputs = ["onchain_heat", "spread"]

    async def decide(self, ctx: AgentContext) -> dict:
        heat_env = await ctx.indicator("onchain_heat")
        spread_env = await ctx.indicator("spread")

        heat_meta = heat_env.get("meta", {})
        spread_meta = spread_env.get("meta", {})
        stale = bool(heat_meta.get("stale") or spread_meta.get("stale"))
        notes_parts: list[str] = []
        if heat_meta.get("notes"):
            notes_parts.append(f"heat: {heat_meta['notes']}")
        if spread_meta.get("notes"):
            notes_parts.append(f"spread: {spread_meta['notes']}")
        notes = "; ".join(notes_parts) if notes_parts else None

        heat_value = heat_env.get("value") or {}
        spread_value = spread_env.get("value") or {}
        heat_score = float(heat_value.get("score") or 0.0)
        spread_bps = float(spread_value.get("spread_bps") or 0.0)
        wide_book = spread_bps > WIDE_SPREAD_BPS

        if heat_score >= HEAT_HOT and not wide_book:
            stance = "bullish"
            confidence = min(100.0, (heat_score - HEAT_HOT) * (100.0 / 35.0))
        elif heat_score <= HEAT_COLD:
            stance = "bearish"
            confidence = min(100.0, (HEAT_COLD - heat_score) * (100.0 / 35.0))
        else:
            stance = "neutral"
            # Confidence highest at the dead centre of the band.
            mid = (HEAT_HOT + HEAT_COLD) / 2
            confidence = max(0.0, 100.0 - abs(heat_score - mid) * (100.0 / 15.0))

        components = heat_value.get("components") or {}
        base_reasoning = (
            f"Heat {heat_score:.1f} (fill rate {components.get('fill_rate', 0)}, "
            f"TVL {components.get('tvl', 0)}, velocity {components.get('velocity', 0)}). "
            f"Spread {spread_bps:.1f} bps"
            f"{', wide book fading the heat signal' if wide_book else ''}."
        )
        if notes:
            base_reasoning = f"{base_reasoning} Notes: {notes}."

        reasoning = await maybe_narrate(
            agent_name=self.name,
            stance=stance,
            base_reasoning=base_reasoning,
            extras={
                "heat_score": heat_score,
                "components": components,
                "spread_bps": spread_bps,
                "wide_book": wide_book,
                "stale": stale,
            },
        )

        return {
            "stance": stance,
            "confidence": round(confidence, 1),
            "reasoning": reasoning,
            "inputs_seen": ["onchain_heat", "spread"],
            "ts": int(time.time()),
            "meta": {"stale": stale, "notes": notes},
        }


register(GeneralAgent())
