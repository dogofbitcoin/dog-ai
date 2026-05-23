from __future__ import annotations

import pytest

from backend.indicators.vwap import VwapIndicator


@pytest.mark.asyncio
async def test_vwap_drops_trades_outside_window(fake_ctx):
    ind = VwapIndicator()
    ind.window_seconds = 60
    now = 10_000
    ctx = fake_ctx(
        now_ts=now,
        payloads={
            ("kraken", "trades"): {
                "pair": "DOGBTC",
                "trades": [
                    {"ts": now - 120, "price": 1.0, "volume": 1.0, "side": "buy"},
                    {"ts": now - 30, "price": 2.0, "volume": 1.0, "side": "buy"},
                    {"ts": now - 10, "price": 3.0, "volume": 1.0, "side": "sell"},
                ],
                "synthetic": False,
            }
        },
    )
    env = await ind.compute(ctx)
    assert env["value"]["samples"] == 2
    assert env["value"]["vwap"] == pytest.approx((2.0 + 3.0) / 2.0)


@pytest.mark.asyncio
async def test_vwap_returns_stale_when_no_trades(fake_ctx):
    ind = VwapIndicator()
    ctx = fake_ctx(
        now_ts=5_000,
        payloads={("kraken", "trades"): {"trades": [], "pair": "DOGBTC"}},
    )
    env = await ind.compute(ctx)
    assert env["value"] is None
    assert env["meta"]["stale"] is True
