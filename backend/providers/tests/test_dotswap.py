"""DotSwap provider tests.

No network. Tests patch the internal `_fetch_snapshot` to exercise the public
interface, the cache, and the error envelope contract.
"""

from __future__ import annotations

import pytest

from backend.providers.dotswap import DotSwapProvider


@pytest.mark.asyncio
async def test_fetch_returns_error_when_nexus_url_missing(monkeypatch):
    monkeypatch.delenv("NEXUS_URL", raising=False)
    monkeypatch.delenv("NEXUS_API_KEY", raising=False)
    p = DotSwapProvider()
    out = await p.fetch()
    assert out == {"error": "missing NEXUS_URL"}


@pytest.mark.asyncio
async def test_fetch_returns_error_when_api_key_missing(monkeypatch):
    monkeypatch.setenv("NEXUS_URL", "http://example.test")
    monkeypatch.delenv("NEXUS_API_KEY", raising=False)
    p = DotSwapProvider()
    out = await p.fetch()
    assert out == {"error": "missing NEXUS_API_KEY"}


@pytest.mark.asyncio
async def test_fetch_caches_successful_snapshot(monkeypatch):
    monkeypatch.setenv("NEXUS_URL", "http://example.test")
    monkeypatch.setenv("NEXUS_API_KEY", "x")
    p = DotSwapProvider()
    calls = {"n": 0}

    async def fake_snapshot() -> dict:
        calls["n"] += 1
        return {
            "tick1": p.tick1,
            "tick2": p.tick2,
            "ts": 1,
            "source": "dotswap",
            "floor_sats_per_dog": 0.94,
            "floor_btc": 9.4e-9,
            "volume_24h_btc": 10.0,
            "fill_count_1h": 12,
            "fill_count_24h": 200,
            "tvl_dog": 100_000_000.0,
            "recent_fills": [],
            "fees": {},
        }

    monkeypatch.setattr(p, "_fetch_snapshot", fake_snapshot)

    a = await p.fetch()
    b = await p.fetch()
    assert a == b
    assert calls["n"] == 1, "second fetch should be served from cache"


@pytest.mark.asyncio
async def test_fetch_does_not_cache_errors(monkeypatch):
    monkeypatch.setenv("NEXUS_URL", "http://example.test")
    monkeypatch.setenv("NEXUS_API_KEY", "x")
    p = DotSwapProvider()
    calls = {"n": 0}

    async def fake_snapshot() -> dict:
        calls["n"] += 1
        return {"error": "boom"}

    monkeypatch.setattr(p, "_fetch_snapshot", fake_snapshot)
    await p.fetch()
    await p.fetch()
    assert calls["n"] == 2, "errors must not poison the cache"
