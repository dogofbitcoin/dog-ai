"""Kraken provider.

Wraps the Kraken CLI installed on the host. Read only in v0.1. No orders are
placed by this module. Operator actions are emitted as dry run CLI strings.

A note on the default pair. The spec sets `KRAKEN_PAIR=DOGBTC`, but Kraken does
not list a direct DOG/BTC market for the $DOG Rune (only DOGUSD and DOGEUR).
This provider synthesises DOG/BTC from the two underlying tickers when asked
for `DOGBTC`. Direct pairs pass through unchanged.

Synthesis formulas:
  DOG/BTC bid = DOGUSD bid / XBTUSD ask
  DOG/BTC ask = DOGUSD ask / XBTUSD bid
  DOG/BTC last = DOGUSD last / XBTUSD last
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
from typing import Any

from ..log import log
from . import register
from .base import Provider

SYNTHETIC_DOGBTC = "DOGBTC"
DOGBTC_LEGS = ("DOGUSD", "XBTUSD")


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _normalize_ticker_key(pair: str, raw: dict) -> dict | None:
    """Kraken sometimes returns canonical asset codes (XXBTZUSD for XBTUSD).
    Resolve the response key for the requested pair."""
    if pair in raw:
        return raw[pair]
    aliases = {
        "XBTUSD": "XXBTZUSD",
        "XBTEUR": "XXBTZEUR",
    }
    alt = aliases.get(pair)
    if alt and alt in raw:
        return raw[alt]
    # last resort, just take the first value if there's exactly one
    if len(raw) == 1:
        return next(iter(raw.values()))
    return None


class KrakenProvider(Provider):
    name = "kraken"
    kind = "market"

    def __init__(self) -> None:
        self.cli_path = os.getenv("KRAKEN_CLI_PATH", "kraken")
        self.pair = os.getenv("KRAKEN_PAIR", "DOGBTC")

    # ------- public surface -------

    async def fetch(self, **kwargs: Any) -> dict:
        endpoint = kwargs.get("endpoint", "ticker")
        pair = kwargs.get("pair", self.pair)
        try:
            if endpoint in ("balance", "open-orders", "volume"):
                if endpoint == "balance":
                    return await self._balance()
                if endpoint == "open-orders":
                    return await self._open_orders()
                return await self._volume(pair=pair)
            if pair == SYNTHETIC_DOGBTC:
                return await self._fetch_synthetic_dogbtc(endpoint)
            if endpoint == "ticker":
                return await self._ticker(pair)
            if endpoint == "trades":
                return await self._trades(pair, count=int(kwargs.get("count", 20)))
            if endpoint == "orderbook":
                return await self._orderbook(pair, count=int(kwargs.get("count", 10)))
            if endpoint == "trades-history":
                return await self._trades_history(pair=pair, count=int(kwargs.get("count", 20)))
            if endpoint == "spreads":
                return await self._spreads(pair=pair)
            return {"error": f"unknown endpoint {endpoint!r}"}
        except Exception as e:  # never raise out
            log.warning("kraken.fetch failed endpoint=%s pair=%s err=%s", endpoint, pair, e)
            return {"error": str(e)}

    async def health(self) -> dict:
        started = time.monotonic()
        if not shutil.which(self.cli_path):
            return {
                "ok": False,
                "latency_ms": 0,
                "note": f"kraken CLI not on PATH (KRAKEN_CLI_PATH={self.cli_path})",
            }
        try:
            raw = await self._run(["status", "-o", "json"])
            latency = int((time.monotonic() - started) * 1000)
            status = raw.get("status") if isinstance(raw, dict) else None
            ok = status == "online"
            note = "" if ok else f"status={status}"
            return {"ok": ok, "latency_ms": latency, "note": note}
        except Exception as e:
            return {
                "ok": False,
                "latency_ms": int((time.monotonic() - started) * 1000),
                "note": str(e),
            }

    # ------- endpoint helpers -------

    async def _ticker(self, pair: str) -> dict:
        raw = await self._run(["ticker", pair, "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        tk = _normalize_ticker_key(pair, raw) if isinstance(raw, dict) else None
        if not tk:
            return {"error": f"no ticker for {pair} in response"}
        return {
            "pair": pair,
            "ts": int(time.time()),
            "source": self.name,
            "bid": _to_float(tk.get("b", [0])[0]),
            "ask": _to_float(tk.get("a", [0])[0]),
            "last": _to_float(tk.get("c", [0])[0]),
            "vwap_24h": _to_float(tk.get("p", [0, 0])[1]),
            "volume_24h": _to_float(tk.get("v", [0, 0])[1]),
            "synthetic": False,
        }

    async def _trades(self, pair: str, count: int) -> dict:
        raw = await self._run(["trades", pair, "--count", str(count), "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        # The CLI returns {<pair_key>: [[price, volume, ts, side, type, misc, id], ...], "last": "..."}.
        rows: list = []
        if isinstance(raw, dict):
            container = _normalize_ticker_key(pair, {k: v for k, v in raw.items() if k != "last"})
            if isinstance(container, list):
                rows = container
        out_trades: list[dict] = []
        for r in rows:
            if isinstance(r, list) and len(r) >= 4:
                out_trades.append(
                    {
                        "price": _to_float(r[0]),
                        "volume": _to_float(r[1]),
                        "ts": int(_to_float(r[2])),
                        "side": "buy" if r[3] == "b" else "sell" if r[3] == "s" else "",
                    }
                )
            elif isinstance(r, dict):
                out_trades.append(
                    {
                        "price": _to_float(r.get("price")),
                        "volume": _to_float(r.get("volume") or r.get("qty")),
                        "ts": int(_to_float(r.get("time") or r.get("ts"))),
                        "side": r.get("side", ""),
                    }
                )
        return {
            "pair": pair,
            "ts": int(time.time()),
            "source": self.name,
            "trades": out_trades,
            "synthetic": False,
        }

    async def _orderbook(self, pair: str, count: int) -> dict:
        raw = await self._run(["orderbook", pair, "--count", str(count), "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        book = _normalize_ticker_key(pair, raw) if isinstance(raw, dict) else None
        if not book:
            return {"error": f"no orderbook for {pair} in response"}
        bids = [(_to_float(p), _to_float(v)) for p, v, *_ in book.get("bids", [])]
        asks = [(_to_float(p), _to_float(v)) for p, v, *_ in book.get("asks", [])]
        return {
            "pair": pair,
            "ts": int(time.time()),
            "source": self.name,
            "bids": bids,
            "asks": asks,
            "synthetic": False,
        }

    # ------- account and history endpoints -------

    async def _balance(self) -> dict:
        raw = await self._run(["balance", "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        return {"ts": int(time.time()), "source": self.name, "balances": raw}

    async def _open_orders(self) -> dict:
        raw = await self._run(["open-orders", "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        orders = raw.get("open", {}) if isinstance(raw, dict) else {}
        return {
            "ts": int(time.time()),
            "source": self.name,
            "count": len(orders),
            "orders": orders,
        }

    async def _trades_history(self, pair: str, count: int) -> dict:
        raw = await self._run(["trades-history", "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        trades = raw.get("trades", {}) if isinstance(raw, dict) else {}
        filtered = []
        for tid, t in (trades.items() if isinstance(trades, dict) else []):
            if pair == SYNTHETIC_DOGBTC:
                if t.get("pair") not in ("DOGUSD", "XDOGUSD"):
                    continue
            elif t.get("pair") not in (pair, f"X{pair}", f"{pair}Z"):
                continue
            filtered.append({
                "txid": tid,
                "pair": t.get("pair"),
                "side": t.get("type"),
                "price": _to_float(t.get("price")),
                "volume": _to_float(t.get("vol")),
                "cost": _to_float(t.get("cost")),
                "fee": _to_float(t.get("fee")),
                "ts": int(_to_float(t.get("time"))),
            })
        filtered.sort(key=lambda x: x["ts"], reverse=True)
        return {
            "ts": int(time.time()),
            "source": self.name,
            "pair": pair,
            "trades": filtered[:count],
            "total_count": len(filtered),
        }

    async def _volume(self, pair: str) -> dict:
        raw = await self._run(["volume", "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        return {
            "ts": int(time.time()),
            "source": self.name,
            "volume": raw.get("volume"),
            "currency": raw.get("currency"),
            "fees": raw.get("fees", {}),
        }

    async def _spreads(self, pair: str) -> dict:
        target = "DOGUSD" if pair == SYNTHETIC_DOGBTC else pair
        raw = await self._run(["spreads", target, "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        spreads_data = _normalize_ticker_key(target, {k: v for k, v in raw.items() if k != "last"}) if isinstance(raw, dict) else None
        entries = []
        if isinstance(spreads_data, list):
            for s in spreads_data[-20:]:
                if isinstance(s, list) and len(s) >= 3:
                    entries.append({
                        "ts": int(_to_float(s[0])),
                        "bid": _to_float(s[1]),
                        "ask": _to_float(s[2]),
                    })
        return {
            "ts": int(time.time()),
            "source": self.name,
            "pair": target,
            "spreads": entries,
        }

    # ------- dead man's switch -------

    async def cancel_after(self, timeout_seconds: int = 600) -> dict:
        """Activate the dead man's switch. All open orders cancel if not refreshed."""
        raw = await self._run(["order", "cancel-after", str(timeout_seconds), "-o", "json"])
        if isinstance(raw, dict) and "error" in raw:
            return raw
        return {"ts": int(time.time()), "timeout_s": timeout_seconds, "result": raw}

    # ------- synthetic DOG/BTC -------

    async def _fetch_synthetic_dogbtc(self, endpoint: str) -> dict:
        if endpoint == "ticker":
            dog = await self._ticker("DOGUSD")
            btc = await self._ticker("XBTUSD")
            if "error" in dog or "error" in btc:
                return {"error": f"synthetic ticker failed dog={dog} btc={btc}"}
            return {
                "pair": SYNTHETIC_DOGBTC,
                "ts": int(time.time()),
                "source": self.name,
                "bid": dog["bid"] / btc["ask"] if btc["ask"] else 0.0,
                "ask": dog["ask"] / btc["bid"] if btc["bid"] else 0.0,
                "last": dog["last"] / btc["last"] if btc["last"] else 0.0,
                "vwap_24h": dog["vwap_24h"] / btc["vwap_24h"] if btc["vwap_24h"] else 0.0,
                "volume_24h": dog["volume_24h"],  # in DOG units
                "synthetic": True,
                "legs": {"dog": dog, "btc": btc},
            }

        # For trades and orderbook, convert each price using current XBTUSD mid.
        btc = await self._ticker("XBTUSD")
        if "error" in btc:
            return {"error": f"synthetic {endpoint} needs XBTUSD: {btc['error']}"}
        btc_mid = (btc["bid"] + btc["ask"]) / 2 if (btc["bid"] and btc["ask"]) else btc["last"]
        if not btc_mid:
            return {"error": "synthetic conversion failed: XBTUSD mid is zero"}

        if endpoint == "trades":
            base = await self._trades("DOGUSD", count=20)
            if "error" in base:
                return base
            base["pair"] = SYNTHETIC_DOGBTC
            base["synthetic"] = True
            base["btc_mid"] = btc_mid
            for t in base["trades"]:
                t["price"] = t["price"] / btc_mid if btc_mid else 0.0
            return base

        if endpoint == "orderbook":
            base = await self._orderbook("DOGUSD", count=10)
            if "error" in base:
                return base
            base["pair"] = SYNTHETIC_DOGBTC
            base["synthetic"] = True
            base["btc_mid"] = btc_mid
            base["bids"] = [(p / btc_mid, v) for p, v in base["bids"]]
            base["asks"] = [(p / btc_mid, v) for p, v in base["asks"]]
            return base

        return {"error": f"synthetic does not support endpoint {endpoint!r}"}

    # ------- subprocess plumbing -------

    async def _run(self, args: list[str]) -> Any:
        cmd = [self.cli_path, *args]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        if proc.returncode != 0:
            err_text = stderr.decode("utf-8", "replace").strip() or stdout.decode("utf-8", "replace")
            raise RuntimeError(f"kraken cli exit={proc.returncode}: {err_text}")
        text = stdout.decode("utf-8", "replace")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"kraken cli returned non json: {text[:200]}") from e

    # ------- dry run action helper -------

    def build_action_command(
        self,
        side: str,
        volume: float,
        pair: str | None = None,
        price: float | None = None,
        order_type: str = "limit",
        validate: bool = True,
    ) -> str:
        """Return the kraken CLI string the operator should run.
        v0.1 never executes orders from the dashboard."""
        pair = pair or self.pair
        if pair == SYNTHETIC_DOGBTC:
            # The operator cannot place a synthetic order; surface the underlying leg.
            pair = "DOGUSD"
        parts = [self.cli_path, "order", side, pair, f"{volume}"]
        if order_type:
            parts += ["--type", order_type]
        if price is not None:
            parts += ["--price", f"{price}"]
        if validate:
            parts.append("--validate")
        parts += ["-o", "json"]
        return " ".join(parts)


register(KrakenProvider())
