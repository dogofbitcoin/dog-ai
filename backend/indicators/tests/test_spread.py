from __future__ import annotations

import pytest

from backend.indicators.spread import SpreadIndicator


@pytest.mark.asyncio
async def test_spread_computes_bps_from_bid_ask(fake_ctx):
    ind = SpreadIndicator()
    ctx = fake_ctx(
        now_ts=1_000_000,
        payloads={
            "kraken": {
                "pair": "DOGBTC",
                "ts": 1_000_000,
                "bid": 9.4e-9,
                "ask": 9.5e-9,
                "last": 9.45e-9,
                "synthetic": True,
            }
        },
    )
    env = await ind.compute(ctx)
    v = env["value"]
    mid = (9.4e-9 + 9.5e-9) / 2
    expected_bps = ((9.5e-9 - 9.4e-9) / mid) * 10_000
    # Indicator rounds bps to 2 decimals; compare with abs=0.01.
    assert v["spread_bps"] == pytest.approx(expected_bps, abs=0.01)
    assert env["meta"]["stale"] is False


@pytest.mark.asyncio
async def test_spread_returns_stale_envelope_on_provider_error(fake_ctx):
    ind = SpreadIndicator()
    ctx = fake_ctx(now_ts=1, payloads={"kraken": {"error": "boom"}})
    env = await ind.compute(ctx)
    assert env["value"] is None
    assert env["meta"]["stale"] is True
    assert "boom" in env["meta"]["notes"]
