"""Alpha agent.

Reads the `signal_quality` indicator and produces a stance about how much to
trust the rest of the dashboard right now. Alpha does not have an opinion on
price or direction; its job is purely to gate confidence.

Stances:
  confident  signal quality is solid, the rest of the dashboard is reliable
  tentative  partial coverage, treat numbers as directional not exact
  blind      data is missing or stale, do not act on the dashboard

The mapping is rule based and deterministic. If `ANTHROPIC_API_KEY` is set,
the reasoning string can optionally be rewritten by a small LLM call via
`narrate.rewrite_reasoning`. The stance itself stays rule based so behaviour
is testable.
"""

from __future__ import annotations

import time

from . import register
from .base import Agent, AgentContext
from .narrate import maybe_narrate

CONFIDENT_THRESHOLD = 70.0
TENTATIVE_THRESHOLD = 30.0


def _stance_for_score(score: float, stale: bool) -> tuple[str, float]:
    if stale or score < TENTATIVE_THRESHOLD:
        return "blind", max(0.0, 50.0 - score)
    if score >= CONFIDENT_THRESHOLD:
        # Confidence rises linearly from 0 at threshold to 100 at score 100.
        return "confident", min(100.0, (score - CONFIDENT_THRESHOLD) * (100.0 / 30.0))
    # Tentative band
    return "tentative", (score - TENTATIVE_THRESHOLD) * (100.0 / (CONFIDENT_THRESHOLD - TENTATIVE_THRESHOLD))


class AlphaAgent(Agent):
    name = "alpha"
    inputs = ["signal_quality"]

    async def decide(self, ctx: AgentContext) -> dict:
        env = await ctx.indicator("signal_quality")
        meta = env.get("meta", {})
        notes = meta.get("notes")
        stale = bool(meta.get("stale"))
        value = env.get("value") or {}
        score = float(value.get("score") or 0.0)
        components = value.get("components") or {}

        stance, confidence = _stance_for_score(score, stale)
        base_reasoning = (
            f"Signal quality {score:.1f}. Freshness {components.get('freshness', 0)}, "
            f"depth {components.get('depth', 0)}, agreement {components.get('agreement', 0)}."
        )
        if notes:
            base_reasoning = f"{base_reasoning} Notes: {notes}."

        reasoning = await maybe_narrate(
            agent_name=self.name,
            stance=stance,
            base_reasoning=base_reasoning,
            extras={"score": score, "components": components, "stale": stale},
        )

        return {
            "stance": stance,
            "confidence": round(confidence, 1),
            "reasoning": reasoning,
            "inputs_seen": ["signal_quality"],
            "ts": int(env.get("ts") or time.time()),
            "meta": {"stale": stale, "notes": notes},
        }


register(AlphaAgent())
