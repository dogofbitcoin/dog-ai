"""Kraken agent — the exchange specialist.

Where Alpha gates confidence and General Ghost reads direction, Kraken focuses
on the exchange itself: how the book looks right now, what the last Trader
fill actually ran as a CLI command, what the next fill would look like as a
dry-run preview, and which of the bundled SKILL.md packages is most relevant
to the current regime.

The character: a dog in a purple hoodie with a Kraken logo. Art lands later.

This agent is deterministic. No LLM call. It reads the spread indicator + the
Trader's state and composes a structured envelope. The dashboard renders each
section as its own block.
"""

from __future__ import annotations

import time

from ..providers.kraken import KrakenProvider
from . import register
from .base import Agent, AgentContext


SKILL_RULES = [
    # (predicate(spread_bps, signal_quality, heat) -> bool, skill_name, summary)
    (
        lambda bps, sq, h: bps is not None and bps > 60,
        "kraken-fee-optimization",
        "Wide spread, lean on maker orders. Use --type post and price at the bid to capture the 0.23 percent maker fee.",
    ),
    (
        lambda bps, sq, h: sq is not None and sq < 60,
        "kraken-error-recovery",
        "Data quality is low, treat fills with suspicion. Use --validate to dry run, then confirm before submitting.",
    ),
    (
        lambda bps, sq, h: h is not None and h > 75,
        "kraken-spot-execution",
        "Heat spiking, expect slippage. Ladder via batch orders and respect cancel-after deadman switch.",
    ),
    (
        lambda bps, sq, h: h is not None and h < 30,
        "kraken-paper-strategy",
        "Cool regime, ideal time to validate new strategies in paper before pushing live.",
    ),
    (
        lambda bps, sq, h: bps is not None and bps < 30,
        "kraken-dca-strategy",
        "Spread tight, classic DCA window. Steady small buys at the bid stack up cheaply.",
    ),
]
DEFAULT_SKILL = ("kraken-shared", "Stay on the documented happy path. Validate, parse JSON, never assume direction.")


class KrakenAgent(Agent):
    name = "kraken"
    inputs = ["spread", "signal_quality", "onchain_heat"]

    def __init__(self) -> None:
        self.kraken_provider = KrakenProvider()

    async def decide(self, ctx: AgentContext) -> dict:
        # Pull the indicators we declared.
        spread_env = await ctx.indicator("spread")
        sq_env = await ctx.indicator("signal_quality")
        heat_env = await ctx.indicator("onchain_heat")

        spread = (spread_env.get("value") or {}) if spread_env else {}
        sq_val = (sq_env.get("value") or {}) if sq_env else {}
        heat_val = (heat_env.get("value") or {}) if heat_env else {}
        spread_bps = float(spread.get("spread_bps") or 0.0)
        sq_score = float(sq_val.get("score") or 0.0)
        heat_score = float(heat_val.get("score") or 0.0)

        # Live Kraken ticker on the synthetic and the real DOGUSD pair, side by side.
        synthetic_ticker = await self.kraken_provider.fetch(endpoint="ticker", pair="DOGBTC")
        direct_ticker = await self.kraken_provider.fetch(endpoint="ticker", pair="DOGUSD")

        # Pull the Trader's last fill command (if it has one) from the shared registry.
        from . import get as get_agent
        trader_state = None
        try:
            trader_state = get_agent("trader").state  # type: ignore[attr-defined]
        except Exception:
            trader_state = None
        last_fill_cmd = None
        if trader_state:
            for entry in trader_state.get("decision_log") or []:
                cmd = (entry.get("result") or {}).get("command")
                if cmd:
                    last_fill_cmd = {
                        "ts": entry.get("ts"),
                        "command": cmd,
                        "decision": entry.get("decision"),
                    }
                    break

        # Build a dry run preview command for "if Trader said buy 2000 DOG right now".
        # Uses the kraken provider's helper, no real order is built or submitted.
        dry_run_buy = self.kraken_provider.build_action_command(
            side="buy",
            volume=2000,
            pair="DOGUSD",
            price=float(direct_ticker.get("bid") or 0.0) if isinstance(direct_ticker, dict) and "error" not in direct_ticker else None,
            order_type="limit",
            validate=True,
        )
        dry_run_sell = self.kraken_provider.build_action_command(
            side="sell",
            volume=2000,
            pair="DOGUSD",
            price=float(direct_ticker.get("ask") or 0.0) if isinstance(direct_ticker, dict) and "error" not in direct_ticker else None,
            order_type="limit",
            validate=True,
        )

        # Skill in focus
        skill_name, skill_summary = DEFAULT_SKILL
        for predicate, name, summary in SKILL_RULES:
            try:
                if predicate(spread_bps, sq_score, heat_score):
                    skill_name, skill_summary = name, summary
                    break
            except Exception:
                continue

        # A short stance for the dashboard header.
        stance = "watching"
        if spread_bps > 80:
            stance = "wide-book"
        elif spread_bps < 25:
            stance = "tight-book"
        if sq_score < 50:
            stance = "low-signal"

        return {
            "stance": stance,
            "confidence": round(max(0.0, min(100.0, sq_score)), 1),
            "reasoning": (
                f"Kraken DOGUSD bid {_safe_get(direct_ticker, 'bid', 0.0):.6f}, ask "
                f"{_safe_get(direct_ticker, 'ask', 0.0):.6f}, spread {spread_bps:.1f} bps. "
                f"Skill in focus: {skill_name}."
            ),
            "inputs_seen": self.inputs,
            "ts": int(time.time()),
            "meta": {
                "stale": bool(spread_env.get("meta", {}).get("stale")),
                "notes": None,
            },
            "kraken": {
                "ticker": {
                    "synthetic_dogbtc": _ticker_block(synthetic_ticker),
                    "dogusd": _ticker_block(direct_ticker),
                },
                "last_fill_command": last_fill_cmd,
                "dry_run_preview": {
                    "buy_2000_at_bid": dry_run_buy,
                    "sell_2000_at_ask": dry_run_sell,
                },
                "skill_in_focus": {"name": skill_name, "summary": skill_summary},
                "regime": {
                    "spread_bps": spread_bps,
                    "signal_quality": sq_score,
                    "onchain_heat": heat_score,
                },
            },
        }


def _ticker_block(t) -> dict:
    if not isinstance(t, dict) or "error" in t:
        return {"available": False, "error": (t or {}).get("error", "unavailable")}
    return {
        "available": True,
        "pair": t.get("pair"),
        "bid": t.get("bid"),
        "ask": t.get("ask"),
        "last": t.get("last"),
        "vwap_24h": t.get("vwap_24h"),
        "volume_24h": t.get("volume_24h"),
        "synthetic": t.get("synthetic", False),
    }


def _safe_get(d, k, default):
    if isinstance(d, dict):
        try:
            return float(d.get(k) or default)
        except (TypeError, ValueError):
            return default
    return default


register(KrakenAgent())
