from __future__ import annotations

import pytest

from backend.indicators.signal_quality import SignalQualityIndicator


@pytest.mark.asyncio
async def test_full_score_when_fresh_deep_and_aligned(fake_ctx):
    ind = SignalQualityIndicator()
    now = 100
    ctx = fake_ctx(
        now_ts=now,
        payloads={
            ("kraken", "ticker"): {
                "pair": "DOGBTC",
                "ts": now - 5,
                "bid": 9.5e-9,
                "ask": 9.6e-9,
            },
            ("kraken", "orderbook"): {
                "bids": [(0.0007, 1_000_000), (0.0006, 200_000), (0.0005, 100_000)],
                "asks": [(0.00072, 1_000_000), (0.00073, 200_000), (0.00074, 100_000)],
            },
            "dotswap": {
                "ts": now - 5,
                "floor_btc": 9.5e-9,
                "volume_24h_btc": 10.0,
                "holder_count": 15000,
                "fill_count_1h": 120,
                "recent_fills": [],
            },
        },
    )
    env = await ind.compute(ctx)
    assert env["value"]["score"] == pytest.approx(100.0, rel=1e-3)
    assert env["meta"]["stale"] is False


@pytest.mark.asyncio
async def test_zero_score_when_everything_is_broken(fake_ctx):
    ind = SignalQualityIndicator()
    ctx = fake_ctx(
        now_ts=1_000,
        payloads={
            ("kraken", "ticker"): {"error": "down"},
            ("kraken", "orderbook"): {"error": "down"},
            "dotswap": {"error": "down"},
        },
    )
    env = await ind.compute(ctx)
    assert env["value"]["score"] == 0
    assert env["meta"]["stale"] is True
    assert "kraken ticker" in env["meta"]["notes"]
    assert "dotswap" in env["meta"]["notes"]
