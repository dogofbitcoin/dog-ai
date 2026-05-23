from __future__ import annotations

import pytest

from backend.agents.alpha import AlphaAgent


def _envelope(score: float, stale: bool = False, notes: str | None = None) -> dict:
    return {
        "value": {
            "score": score,
            "components": {"freshness": 0, "depth": 0, "agreement": 0},
            "age_seconds": 0,
        },
        "ts": 1,
        "meta": {"stale": stale, "sources": ["kraken", "dotswap"], "notes": notes},
    }


@pytest.mark.asyncio
async def test_confident_above_threshold(fake_agent_ctx):
    ag = AlphaAgent()
    ctx = fake_agent_ctx(now_ts=1, envelopes={"signal_quality": _envelope(85.0)})
    out = await ag.decide(ctx)
    assert out["stance"] == "confident"
    assert out["confidence"] > 0
    assert out["meta"]["stale"] is False


@pytest.mark.asyncio
async def test_tentative_in_middle_band(fake_agent_ctx):
    ag = AlphaAgent()
    ctx = fake_agent_ctx(now_ts=1, envelopes={"signal_quality": _envelope(50.0)})
    out = await ag.decide(ctx)
    assert out["stance"] == "tentative"


@pytest.mark.asyncio
async def test_blind_when_stale(fake_agent_ctx):
    ag = AlphaAgent()
    ctx = fake_agent_ctx(
        now_ts=1, envelopes={"signal_quality": _envelope(80.0, stale=True, notes="x")}
    )
    out = await ag.decide(ctx)
    assert out["stance"] == "blind"
    assert out["meta"]["stale"] is True
