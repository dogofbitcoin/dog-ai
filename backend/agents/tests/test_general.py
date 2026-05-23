from __future__ import annotations

import pytest

from backend.agents.general import GeneralAgent


def _heat(score: float) -> dict:
    return {
        "value": {
            "score": score,
            "components": {"fill_rate": 0, "holder": 0, "velocity": 0},
            "raw": {"fill_count_1h": 0, "holder_count": 0, "volume_24h_btc": 0.0},
        },
        "ts": 1,
        "meta": {"stale": False, "sources": ["dotswap"], "notes": None},
    }


def _spread(bps: float) -> dict:
    return {
        "value": {"pair": "DOGBTC", "bid": 1, "ask": 1, "mid": 1, "spread_bps": bps, "synthetic": True},
        "ts": 1,
        "meta": {"stale": False, "sources": ["kraken"], "notes": None},
    }


@pytest.mark.asyncio
async def test_bullish_hot_heat_and_tight_book(fake_agent_ctx):
    ag = GeneralAgent()
    ctx = fake_agent_ctx(
        now_ts=1,
        envelopes={"onchain_heat": _heat(80.0), "spread": _spread(30.0)},
    )
    out = await ag.decide(ctx)
    assert out["stance"] == "bullish"


@pytest.mark.asyncio
async def test_neutral_when_book_is_wide(fake_agent_ctx):
    ag = GeneralAgent()
    ctx = fake_agent_ctx(
        now_ts=1,
        envelopes={"onchain_heat": _heat(80.0), "spread": _spread(150.0)},
    )
    out = await ag.decide(ctx)
    assert out["stance"] == "neutral"


@pytest.mark.asyncio
async def test_bearish_when_heat_is_cold(fake_agent_ctx):
    ag = GeneralAgent()
    ctx = fake_agent_ctx(
        now_ts=1,
        envelopes={"onchain_heat": _heat(20.0), "spread": _spread(30.0)},
    )
    out = await ag.decide(ctx)
    assert out["stance"] == "bearish"
