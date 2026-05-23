"""DotSwap provider (Nexus backed).

On chain data for the $DOG Rune pulled from a DotSwap Nexus node. v0.1 ships
with a 60 second in memory cache so dashboards do not hammer the endpoint.
Override the TTL with `DOTSWAP_CACHE_TTL=0` to disable.

The provider never raises. On any failure it returns {"error": "..."}.

Env contract:
  NEXUS_URL          base URL of the Nexus node (e.g. http://1.2.3.4:17610)
  NEXUS_API_KEY      X-API-Key header value
  POOL_TICK1         rune tick (e.g. "DOG.GO.TO.THE.MOON" using middots)
  POOL_TICK1_COIN_TYPE
  POOL_TICK2         "BTC"
  POOL_TICK2_COIN_TYPE
  DOTSWAP_CACHE_TTL  seconds (default 60)
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


DEFAULT_TICK1 = "DOG•GO•TO•THE•MOON"  # middot separator


class DotSwapProvider(Provider):
    name = "dotswap"
    kind = "onchain"

    def __init__(self) -> None:
        self.base = os.getenv("NEXUS_URL", "").rstrip("/")
        self.api_key = os.getenv("NEXUS_API_KEY", "")
        self.tick1 = os.getenv("POOL_TICK1", DEFAULT_TICK1)
        self.coin1 = os.getenv("POOL_TICK1_COIN_TYPE", "runes")
        self.tick2 = os.getenv("POOL_TICK2", "BTC")
        self.coin2 = os.getenv("POOL_TICK2_COIN_TYPE", "btc")
        self.cache_ttl = int(os.getenv("DOTSWAP_CACHE_TTL", "60"))
        self._cache: dict[str, tuple[float, dict]] = {}
        self._lock = asyncio.Lock()

    # ------- public surface -------

    async def fetch(self, **kwargs: Any) -> dict:
        if not self.base:
            return {"error": "missing NEXUS_URL"}
        if not self.api_key:
            return {"error": "missing NEXUS_API_KEY"}

        key = f"snapshot:{self.tick1}:{self.tick2}"
        cached = self._read_cache(key)
        if cached is not None:
            return cached

        async with self._lock:
            cached = self._read_cache(key)
            if cached is not None:
                return cached
            payload = await self._fetch_snapshot()
            if "error" not in payload:
                self._write_cache(key, payload)
            return payload

    async def health(self) -> dict:
        started = _now()
        if not self.base:
            return {"ok": False, "latency_ms": 0, "note": "missing NEXUS_URL"}
        if not self.api_key:
            return {"ok": False, "latency_ms": 0, "note": "missing NEXUS_API_KEY"}
        try:
            async with httpx.AsyncClient(timeout=4.0, headers=self._headers()) as client:
                resp = await client.post(
                    f"{self.base}/api/pool/liquid/liquid_info",
                    json={
                        "tick1": {"coin_type": self.coin1, "tick": self.tick1, "token_id": ""},
                        "tick2": {"coin_type": self.coin2, "tick": self.tick2, "token_id": ""},
                    },
                )
            latency = int((_now() - started) * 1000)
            ok = resp.status_code == 200 and resp.json().get("code") in (0, 200)
            return {"ok": ok, "latency_ms": latency, "note": "" if ok else f"http {resp.status_code}"}
        except Exception as e:
            return {
                "ok": False,
                "latency_ms": int((_now() - started) * 1000),
                "note": str(e),
            }

    # ------- internals -------

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key,
        }

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

    def _tick_pair_body(self) -> dict:
        return {
            "tick1": {"coin_type": self.coin1, "tick": self.tick1, "token_id": ""},
            "tick2": {"coin_type": self.coin2, "tick": self.tick2, "token_id": ""},
        }

    async def _fetch_snapshot(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=8.0, headers=self._headers()) as client:
                info_task = client.post(
                    f"{self.base}/api/pool/liquid/liquid_info",
                    json=self._tick_pair_body(),
                )
                hist_task = client.post(
                    f"{self.base}/api/pool/liquid/swap_histories",
                    json={
                        "tick1": self.tick1,
                        "coin_type1": self.coin1,
                        "tick2": self.tick2,
                        "coin_type2": self.coin2,
                        "page": 1,
                        "page_size": 100,
                    },
                )
                info_resp, hist_resp = await asyncio.gather(info_task, hist_task)

            info = self._parse_envelope(info_resp)
            hist = self._parse_envelope(hist_resp)
            items = (hist.get("items") if isinstance(hist, dict) else None) or []

            # Derive floor (sats per DOG, then BTC per DOG) from the latest swap.
            floor_sats_per_dog = 0.0
            for it in items:
                avg = float(it.get("average_price") or 0)
                if avg > 0:
                    floor_sats_per_dog = avg
                    break

            now_s = int(time.time())
            # Normalise swap timestamps; Nexus mixes seconds and milliseconds.
            normalised: list[dict] = []
            for it in items:
                t = int(it.get("time_sec") or 0)
                ts = t // 1000 if t > 10_000_000_000 else t
                btc_leg_is_tick1 = (it.get("tick1") or "").upper() == "BTC"
                sats = float(it.get("tick1_amount") if btc_leg_is_tick1 else it.get("tick2_amount") or 0)
                dog = float(it.get("tick2_amount") if btc_leg_is_tick1 else it.get("tick1_amount") or 0)
                notional_btc = sats / 1e8 if sats else 0.0
                normalised.append(
                    {
                        "ts": ts,
                        "side": "btc_to_dog" if btc_leg_is_tick1 else "dog_to_btc",
                        "dog": dog,
                        "sats": sats,
                        "notional_btc": notional_btc,
                        "avg_price_sats_per_dog": float(it.get("average_price") or 0),
                        "tx_id": it.get("tx_id") or "",
                        "channel": it.get("channel") or "",
                    }
                )

            fills_1h = [f for f in normalised if f["ts"] >= now_s - 3600]
            fills_24h = [f for f in normalised if f["ts"] >= now_s - 86400]
            volume_24h_btc = sum(f["notional_btc"] for f in fills_24h)

            # TVL: read from the most recent swap (in DOG units, divisibility 0).
            tvl_after = 0.0
            for it in items:
                tvl_after = float(it.get("tvl_after_swap") or 0)
                if tvl_after > 0:
                    break

            return {
                "tick1": self.tick1,
                "tick2": self.tick2,
                "ts": now_s,
                "source": self.name,
                "floor_sats_per_dog": floor_sats_per_dog,
                "floor_btc": floor_sats_per_dog / 1e8 if floor_sats_per_dog else 0.0,
                "volume_24h_btc": volume_24h_btc,
                "fill_count_1h": len(fills_1h),
                "fill_count_24h": len(fills_24h),
                "tvl_dog": tvl_after,
                "recent_fills": normalised[:50],
                "fees": {
                    "liquid_buy_pct": float(info.get("liquid_fee_buy_percent") or 0) if isinstance(info, dict) else 0.0,
                    "liquid_sell_pct": float(info.get("liquid_fee_sell_percent") or 0) if isinstance(info, dict) else 0.0,
                    "platform_buy_pct": float(info.get("platform_fee_buy_percent") or 0) if isinstance(info, dict) else 0.0,
                    "platform_sell_pct": float(info.get("platform_fee_sell_percent") or 0) if isinstance(info, dict) else 0.0,
                },
            }
        except Exception as e:
            log.warning("dotswap.fetch failed err=%s", e)
            return {"error": str(e)}

    @staticmethod
    def _parse_envelope(resp: httpx.Response) -> dict:
        try:
            if resp.status_code != 200:
                return {}
            body = resp.json()
            if body.get("code") not in (0, 200):
                return {}
            return body.get("data") or {}
        except Exception:
            return {}


register(DotSwapProvider())
