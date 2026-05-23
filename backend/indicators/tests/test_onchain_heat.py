from __future__ import annotations

import pytest

from backend.indicators.onchain_heat import OnchainHeatIndicator


@pytest.mark.asyncio
async def test_score_caps_at_100_under_extreme_inputs(fake_ctx):
    ind = OnchainHeatIndicator()
    ctx = fake_ctx(
        now_ts=1,
        payloads={
            "dotswap": {
                "ts": 1,
                "fill_count_1h": 100_000,
                "holder_count": 1_000_000,
                "volume_24h_btc": 1.0,
                # 24 hour avg is 1/24 = 0.04167; running 1.0 in 1 hour is ratio 24, capped at 3.
                "recent_fills": [{"notional_btc": 1.0}],
            }
        },
    )
    env = await ind.compute(ctx)
    assert env["value"]["score"] == 100.0
    assert env["meta"]["stale"] is False


@pytest.mark.asyncio
async def test_returns_stale_envelope_when_provider_errors(fake_ctx):
    ind = OnchainHeatIndicator()
    ctx = fake_ctx(now_ts=1, payloads={"dotswap": {"error": "boom"}})
    env = await ind.compute(ctx)
    assert env["value"] is None
    assert env["meta"]["stale"] is True
