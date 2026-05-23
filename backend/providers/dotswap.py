"""DotSwap provider.

On chain data for the $DOG Rune via the DotSwap API. v0.1 ships with a 60 second
in memory cache so demos and refreshes do not hammer the endpoint. Override the
TTL with `DOTSWAP_CACHE_TTL=0` to disable.

The provider never raises. On any failure it returns {"error": "..."}.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx

from ..log import log
from . import register
from .base import Provider


def _now() -> float:
    return time.monotonic()


class DotSwapProvider(Provider):
    name = "dotswap"
    kind = "onchain"

    def __init__(self) -> None:
        self.base = os.getenv("DOTSWAP_API_BASE", "https://api.dotswap.app").rstrip("/")
        self.api_key = os.getenv("DOTSWAP_API_KEY", "")
        self.cache_ttl = int(os.getenv("DOTSWAP_CACHE_TTL", "60"))
        self.rune_default = os.getenv("DOTSWAP_RUNE", "DOG")
        self._cache: dict[str, tuple[float, dict]] = {}
        self._lock = asyncio.Lock()

    # ------- public surface -------

    async def fetch(self, **kwargs: Any) -> dict:
        rune = kwargs.get("rune", self.rune_default)
        if not self.api_key:
            return {"error": "missing DOTSWAP_API_KEY"}

        key = f"snapshot:{rune}"
        cached = self._read_cache(key)
        if cached is not None:
            return cached

        async with self._lock:
            cached = self._read_cache(key)
            if cached is not None:
                return cached
            payload = await self._fetch_snapshot(rune)
            if "error" not in payload:
                self._write_cache(key, payload)
            return payload

    async def health(self) -> dict:
        started = _now()
        if not self.api_key:
            return {"ok": False, "latency_ms": 0, "note": "missing DOTSWAP_API_KEY"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self.base}/health",
                    headers=self._headers(),
                )
            latency = int((_now() - started) * 1000)
            ok = resp.status_code == 200
            return {"ok": ok, "latency_ms": latency, "note": "" if ok else f"http {resp.status_code}"}
        except Exception as e:
            return {
                "ok": False,
                "latency_ms": int((_now() - started) * 1000),
                "note": str(e),
            }

    # ------- internals -------

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key, "accept": "application/json"}

    def _read_cache(self, key: str) -> dict | None:
        if self.cache_ttl <= 0:
            return None
        entry = self._cache.get(key)
        if not entry:
            return None
        stamped, value = entry
        if _now() - stamped > self.cache_ttl:
            return None
        return value

    def _write_cache(self, key: str, value: dict) -> None:
        if self.cache_ttl > 0:
            self._cache[key] = (_now(), value)

    async def _fetch_snapshot(self, rune: str) -> dict:
        """Pull floor, volume, holder count, recent fills, depth. Normalize.

        The DotSwap API surface is not fully public; we issue best effort calls
        to commonly available endpoints and degrade gracefully. The shape
        returned to indicators is stable regardless.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=self._headers()) as client:
                # These endpoints are illustrative. Real paths may differ; the
                # provider handles 4xx by returning the standard error envelope.
                tasks = [
                    client.get(f"{self.base}/runes/{rune}/summary"),
                    client.get(f"{self.base}/runes/{rune}/fills?limit=50"),
                    client.get(f"{self.base}/runes/{rune}/depth?levels=10"),
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            summary = self._json_or_empty(results[0])
            fills = self._json_or_empty(results[1])
            depth = self._json_or_empty(results[2])

            if not summary and not fills and not depth:
                return {"error": "dotswap unreachable"}

            return {
                "rune": rune,
                "ts": int(time.time()),
                "source": self.name,
                "floor_btc": float(summary.get("floor_price_btc") or 0.0),
                "volume_24h_btc": float(summary.get("volume_24h_btc") or 0.0),
                "holder_count": int(summary.get("holders") or 0),
                "fill_count_1h": int(summary.get("fills_1h") or len(fills.get("fills", []) or [])),
                "recent_fills": (fills.get("fills") or [])[:50],
                "depth": {
                    "bids": depth.get("bids") or [],
                    "asks": depth.get("asks") or [],
                },
            }
        except Exception as e:
            log.warning("dotswap.fetch failed err=%s", e)
            return {"error": str(e)}

    @staticmethod
    def _json_or_empty(result: Any) -> dict:
        if isinstance(result, Exception):
            return {}
        try:
            if result.status_code != 200:
                return {}
            return result.json() or {}
        except Exception:
            return {}


register(DotSwapProvider())
