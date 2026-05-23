"""DotSwap provider tests.

No network. Tests patch the internal `_fetch_snapshot` to exercise the public
interface, the cache, and the error envelope contract.
"""

from __future__ import annotations

import pytest

from backend.providers.dotswap import DotSwapProvider


@pytest.mark.asyncio
async def test_fetch_returns_error_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("DOTSWAP_API_KEY", raising=False)
    p = DotSwapProvider()
    out = await p.fetch(rune="DOG")
    assert out == {"error": "missing DOTSWAP_API_KEY"}


@pytest.mark.asyncio
async def test_fetch_caches_successful_snapshot(monkeypatch):
    monkeypatch.setenv("DOTSWAP_API_KEY", "x")
    p = DotSwapProvider()
    calls = {"n": 0}

    async def fake_snapshot(rune: str) -> dict:
        calls["n"] += 1
        return {
            "rune": rune,
            "ts": 1,
            "source": "dotswap",
            "floor_btc": 9.5e-9,
            "volume_24h_btc": 12.0,
            "holder_count": 14_500,
            "fill_count_1h": 120,
            "recent_fills": [],
            "depth": {"bids": [], "asks": []},
        }

    monkeypatch.setattr(p, "_fetch_snapshot", fake_snapshot)

    a = await p.fetch(rune="DOG")
    b = await p.fetch(rune="DOG")
    assert a == b
    assert calls["n"] == 1, "second fetch should be served from cache"


@pytest.mark.asyncio
async def test_fetch_does_not_cache_errors(monkeypatch):
    monkeypatch.setenv("DOTSWAP_API_KEY", "x")
    p = DotSwapProvider()
    calls = {"n": 0}

    async def fake_snapshot(rune: str) -> dict:
        calls["n"] += 1
        return {"error": "boom"}

    monkeypatch.setattr(p, "_fetch_snapshot", fake_snapshot)
    await p.fetch(rune="DOG")
    await p.fetch(rune="DOG")
    assert calls["n"] == 2, "errors must not poison the cache"
