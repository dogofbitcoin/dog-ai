"""Foundation treasury provider.

Fetches on chain BTC balance from mempool.space (free, no auth), combines
with a known DOG rune balance, and merges in the Kraken paper trading
account to show a unified cross venue treasury view.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from ..log import log
from . import register
from .base import Provider

FOUNDATION_ADDRESS = os.getenv("FOUNDATION_BTC_ADDRESS", "")
KNOWN_DOG_BALANCE = float(os.getenv("FOUNDATION_DOG_BALANCE", "1859002"))
MEMPOOL_URL = "https://mempool.space/api"
CACHE_TTL_S = 120


class TreasuryProvider(Provider):
    name = "treasury"
    kind = "wallet"

    def __init__(self) -> None:
        self._cache: dict | None = None
        self._cache_ts: float = 0

    async def fetch(self, **kwargs: Any) -> dict:
        now = time.time()
        if self._cache and (now - self._cache_ts) < CACHE_TTL_S:
            return self._cache
        try:
            result = await self._fetch_live()
            self._cache = result
            self._cache_ts = now
            return result
        except Exception as e:
            log.warning("treasury.fetch failed: %s", e)
            if self._cache:
                return self._cache
            return {"error": str(e)}

    async def _fetch_live(self) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{MEMPOOL_URL}/address/{FOUNDATION_ADDRESS}")
            resp.raise_for_status()
            data = resp.json()

        chain = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})
        funded = chain.get("funded_txo_sum", 0) + mempool.get("funded_txo_sum", 0)
        spent = chain.get("spent_txo_sum", 0) + mempool.get("spent_txo_sum", 0)
        onchain_btc_sats = funded - spent
        onchain_btc = onchain_btc_sats / 1e8
        onchain_dog = KNOWN_DOG_BALANCE

        dog_price_usd = 0.0
        btc_price_usd = 0.0
        try:
            from .kraken import KrakenProvider
            from . import get as get_provider
            kr = get_provider("kraken")
            if isinstance(kr, KrakenProvider):
                xbt_ticker = await kr.fetch(endpoint="ticker", pair="XBTUSD")
                dog_ticker = await kr.fetch(endpoint="ticker", pair="DOGUSD")
                if "error" not in xbt_ticker:
                    btc_price_usd = float(xbt_ticker.get("last", 0))
                if "error" not in dog_ticker:
                    dog_price_usd = float(dog_ticker.get("last", 0))
        except Exception:
            pass

        paper_dog = 0.0
        paper_usd = 0.0
        paper_value = 0.0
        paper_trades = 0
        paper_pnl_pct = 0.0
        try:
            from ..agents import get as get_agent
            trader = get_agent("trader")
            state = trader.state
            balance = state.get("balance") or {}
            portfolio = state.get("portfolio") or {}
            paper_dog = float((balance.get("DOG") or {}).get("total") or 0.0)
            paper_usd = float((balance.get("USD") or {}).get("total") or 0.0)
            paper_value = float(portfolio.get("current_value") or 0.0)
            paper_trades = int(portfolio.get("total_trades") or 0)
            paper_pnl_pct = float(portfolio.get("unrealized_pnl_pct") or 0.0)
        except Exception:
            pass

        onchain_btc_usd = onchain_btc * btc_price_usd
        onchain_dog_usd = onchain_dog * dog_price_usd
        onchain_total_usd = onchain_btc_usd + onchain_dog_usd

        paper_dog_usd = paper_dog * dog_price_usd

        total_dog = onchain_dog + paper_dog
        total_dog_usd = total_dog * dog_price_usd
        total_btc = onchain_btc
        total_btc_usd = onchain_btc_usd
        total_usd_cash = paper_usd
        grand_total_usd = onchain_total_usd + paper_value

        return {
            "ts": int(time.time()),
            "prices": {
                "dog_usd": dog_price_usd,
                "btc_usd": btc_price_usd,
            },
            "onchain": {
                "address": FOUNDATION_ADDRESS,
                "btc": onchain_btc,
                "btc_sats": onchain_btc_sats,
                "btc_usd": round(onchain_btc_usd, 2),
                "dog": onchain_dog,
                "dog_usd": round(onchain_dog_usd, 2),
                "total_usd": round(onchain_total_usd, 2),
            },
            "kraken_paper": {
                "dog": round(paper_dog, 2),
                "dog_usd": round(paper_dog_usd, 2),
                "usd": round(paper_usd, 2),
                "portfolio_value": round(paper_value, 2),
                "total_trades": paper_trades,
                "pnl_pct": round(paper_pnl_pct, 3),
            },
            "totals": {
                "dog": round(total_dog, 2),
                "dog_usd": round(total_dog_usd, 2),
                "btc": total_btc,
                "btc_usd": round(total_btc_usd, 2),
                "usd_cash": round(total_usd_cash, 2),
                "grand_total_usd": round(grand_total_usd, 2),
            },
        }

    async def health(self) -> dict:
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{MEMPOOL_URL}/address/{FOUNDATION_ADDRESS}")
                resp.raise_for_status()
            return {"ok": True, "latency_ms": int((time.monotonic() - started) * 1000), "note": ""}
        except Exception as e:
            return {"ok": False, "latency_ms": int((time.monotonic() - started) * 1000), "note": str(e)}


register(TreasuryProvider())
