"""Trader agent (paper mode, v0.1).

The "main character" agent in Dog of Bitcoin. Where Alpha and General are
passive query-time observers, the Trader runs continuously in the background:
it polls our indicator suite, asks Claude to decide what to do, and executes
the decision against Kraken's built-in paper trading engine.

Hard constraints in v0.1:
  - Paper mode only. The exec path uses `kraken paper buy/sell DOGUSD ...`.
    There is no codepath in this file to a live `kraken order` command.
  - Requires ANTHROPIC_API_KEY. With no key, the agent sits idle and reports
    "not configured" so the dashboard still renders cleanly.
  - Caps: MAX_TRADE_DOG per cycle, MIN_TRADE_COOLDOWN_S between fires,
    HARD_STOP_DRAWDOWN_PCT cuts the loop if paper P&L drops past it.

Claude's system prompt is built from the Kraken-CLI SKILL.md files we
mirrored into `docs/kraken-skills/`. The agent reads Kraken's own playbook
to learn how to operate safely.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

from ..log import log
from ..providers.kraken import KrakenProvider
from . import register
from .base import Agent, AgentContext
from .strategies import DEFAULT_STRATEGY, REGISTRY as STRATEGIES, Strategy, get_strategy

# Tunables (env overridable for the demo).
DECISION_CADENCE_S = int(os.getenv("TRADER_CADENCE_S", "60"))
MAX_POSITION_DOG = float(os.getenv("TRADER_MAX_POSITION_DOG", "1000000"))
HARD_STOP_DRAWDOWN_PCT = float(os.getenv("TRADER_HARD_STOP_PCT", "5.0"))
STARTING_BALANCE_USD = float(os.getenv("TRADER_STARTING_USD", "10000"))
DECISION_MODEL = os.getenv("TRADER_MODEL", "claude-haiku-4-5-20251001")
DECISION_TIMEOUT_S = float(os.getenv("TRADER_DECISION_TIMEOUT", "8.0"))
PAPER_PAIR = os.getenv("TRADER_PAPER_PAIR", "DOGUSD")
SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "kraken-skills"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
LOG_MAX_ENTRIES = 60


def _now() -> int:
    return int(time.time())


class TraderAgent(Agent):
    name = "trader"
    inputs = ["signal_quality", "onchain_heat", "spread", "vwap"]

    def __init__(self) -> None:
        self.cli_path = os.getenv("KRAKEN_CLI_PATH", "kraken")
        self.kraken_provider = KrakenProvider()
        self._skills_blob: str | None = None
        # Persistent state across cycles.
        self.state: dict[str, Any] = {
            "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "initialised": False,
            "halted": False,
            "halt_reason": None,
            "cycle_count": 0,
            "last_decision_ts": 0,
            "last_fill_ts": 0,
            "decision_log": [],   # newest first, capped LOG_MAX_ENTRIES
            "portfolio": {},      # last paper status snapshot
            "balance": {},        # last paper balance snapshot
            "current_intent": None,
            "strategy": os.getenv("TRADER_STRATEGY", DEFAULT_STRATEGY),
        }

    def set_strategy(self, name: str) -> bool:
        """Change active strategy. Returns True if accepted, False if unknown name.
        The change applies on the next decision cycle; in-flight calls are unaffected.
        The change is recorded in the decision_log so it's visible in the dashboard."""
        if name not in STRATEGIES:
            return False
        previous = self.state["strategy"]
        self.state["strategy"] = name
        self._push_log({
            "ts": _now(),
            "indicators": {},
            "decision": {"action": "strategy_change", "size_dog": 0, "reasoning": f"{previous} -> {name}"},
            "result": {"status": "config", "reason": f"switched strategy from {previous} to {name}"},
        })
        return True

    def _strategy(self) -> Strategy:
        return get_strategy(self.state["strategy"])

    # ------- Public interface (used by the FastAPI endpoint) -------

    async def decide(self, ctx: AgentContext) -> dict:
        """Return the dashboard envelope. Reads the in memory state, does not
        run the decision loop itself; that lives in `cycle()`."""
        state = self.state
        envelope = {
            "stance": "halted" if state["halted"] else ("trading" if state["initialised"] else "idle"),
            "confidence": 0.0,
            "reasoning": self._summary_line(),
            "inputs_seen": self.inputs,
            "ts": state["last_decision_ts"] or _now(),
            "meta": {
                "stale": not state["initialised"],
                "notes": state["halt_reason"],
            },
            "trader": {
                "configured": state["configured"],
                "initialised": state["initialised"],
                "halted": state["halted"],
                "cycle_count": state["cycle_count"],
                "last_decision_ts": state["last_decision_ts"],
                "last_fill_ts": state["last_fill_ts"],
                "portfolio": state["portfolio"],
                "balance": state["balance"],
                "current_intent": state["current_intent"],
                "decision_log": state["decision_log"],
                "strategy": {
                    "active": state["strategy"],
                    "title": self._strategy().title,
                    "description": self._strategy().description,
                    "kraken_emphasis": self._strategy().kraken_emphasis,
                    "order_type": self._strategy().order_type,
                },
                "config": {
                    "cadence_s": DECISION_CADENCE_S,
                    "cooldown_s": self._strategy().cooldown_s,
                    "max_trade_dog": self._strategy().max_trade_dog,
                    "max_position_dog": MAX_POSITION_DOG,
                    "hard_stop_pct": HARD_STOP_DRAWDOWN_PCT,
                    "model": DECISION_MODEL,
                    "pair": PAPER_PAIR,
                },
            },
        }
        return envelope

    # ------- Initialisation -------

    async def ensure_paper_initialised(self) -> None:
        if self.state["initialised"]:
            return
        # Check if a paper account already exists. If status succeeds with mode=paper,
        # we are good. If not, run init.
        status = await self._run(["paper", "status", "-o", "json"])
        if isinstance(status, dict) and status.get("mode") == "paper":
            self.state["initialised"] = True
            await self._refresh_portfolio()
            log.info("trader: paper account already live; balance=%s", status.get("current_value"))
            return
        out = await self._run([
            "paper", "init",
            "--balance", str(STARTING_BALANCE_USD),
            "-o", "json",
        ])
        if isinstance(out, dict) and out.get("mode") == "paper":
            self.state["initialised"] = True
            await self._refresh_portfolio()
            log.info("trader: paper initialised balance=%s", STARTING_BALANCE_USD)

    # ------- Main loop step (called by trader_loop) -------

    async def cycle(self, ctx_factory) -> None:
        """Run one decision cycle. ctx_factory builds an AgentContext when
        called with no args, isolating the indicator imports."""
        if not self.state["configured"]:
            return
        if self.state["halted"]:
            return

        await self.ensure_paper_initialised()
        await self._refresh_portfolio()

        self.state["cycle_count"] += 1
        cycle_start_ts = _now()

        # Indicators
        ctx = ctx_factory()
        indicators_snapshot = await self._snapshot_indicators(ctx)

        # Auto-rotate strategy based on regime
        self._auto_rotate_strategy(indicators_snapshot)

        # Decision via Claude
        decision = await self._ask_claude(indicators_snapshot)
        self.state["last_decision_ts"] = cycle_start_ts
        self.state["current_intent"] = decision

        # Execute (with safety gates)
        result = await self._maybe_execute(decision)

        # Log
        self._push_log({
            "ts": cycle_start_ts,
            "indicators": {
                "spread_bps": indicators_snapshot.get("spread_bps"),
                "vwap": indicators_snapshot.get("vwap_sats_per_dog"),
                "signal_quality": indicators_snapshot.get("signal_quality"),
                "onchain_heat": indicators_snapshot.get("onchain_heat"),
            },
            "decision": decision,
            "result": result,
        })

        # Drawdown halt
        pnl_pct = float(self.state["portfolio"].get("unrealized_pnl_pct") or 0.0)
        if pnl_pct < -HARD_STOP_DRAWDOWN_PCT:
            self.state["halted"] = True
            self.state["halt_reason"] = f"drawdown {pnl_pct:.2f}% past hard stop"
            log.warning("trader halted: %s", self.state["halt_reason"])

    # ------- Internals -------

    def _auto_rotate_strategy(self, snap: dict) -> None:
        """Pick the best strategy for the current regime. Runs every cycle
        before the Claude decision call so the prompt reflects the right caps."""
        heat = snap.get("onchain_heat", 0.0)
        sq = snap.get("signal_quality", 0.0)
        spread = snap.get("spread_bps", 0.0)
        stale = snap.get("core_stale", False)
        pnl_pct = float(self.state["portfolio"].get("unrealized_pnl_pct") or 0.0)
        position_dog = float((self.state.get("balance") or {}).get("DOG", {}).get("total") or 0.0)

        portfolio_value = float(self.state["portfolio"].get("current_value") or STARTING_BALANCE_USD)
        cash_usd = float((self.state.get("balance") or {}).get("USD", {}).get("total") or 0.0)
        dog_value_usd = portfolio_value - cash_usd
        dog_pct = (dog_value_usd / portfolio_value * 100) if portfolio_value else 0
        near_cap = position_dog > MAX_POSITION_DOG * 0.75

        if stale or sq < 40:
            pick = "watchdog"
        elif heat < 35:
            pick = "watchdog"
        elif near_cap or dog_pct > 70:
            pick = "sats-stacker"
        elif position_dog > 0 and pnl_pct > 1.0 and heat < 65:
            pick = "sats-stacker"
        elif heat > 60 and sq > 80 and spread < 30 and dog_pct < 50:
            pick = "bite"
        elif heat > 55 and sq > 50 and dog_pct < 60:
            pick = "chase"
        else:
            pick = "dog-dca"

        current = self.state["strategy"]
        if pick != current:
            log.info(
                "auto-rotate strategy: %s -> %s (heat=%.1f sq=%.1f spread=%.1f pnl=%.2f%% dog=%.0f dog_pct=%.1f%%)",
                current, pick, heat, sq, spread, pnl_pct, position_dog, dog_pct,
            )
            self.set_strategy(pick)

    async def _snapshot_indicators(self, ctx: AgentContext) -> dict:
        sq = await ctx.indicator("signal_quality")
        heat = await ctx.indicator("onchain_heat")
        spread = await ctx.indicator("spread")
        vwap = await ctx.indicator("vwap")

        def _v(env):
            return (env or {}).get("value") or {}

        # Only signal_quality and onchain_heat are "must be fresh" for a decision.
        # spread and vwap are nice-to-have context; vwap takes a few minutes to fill
        # its rolling buffer after a restart and that should not paralyse the agent.
        core_stale = any(
            (env or {}).get("meta", {}).get("stale") for env in (sq, heat)
        )
        snap = {
            "signal_quality": float(_v(sq).get("score") or 0.0),
            "onchain_heat": float(_v(heat).get("score") or 0.0),
            "spread_bps": float(_v(spread).get("spread_bps") or 0.0),
            "spread_pair": _v(spread).get("pair"),
            "bid_sats_per_dog": (_v(spread).get("bid") or 0.0) * 1e8,
            "ask_sats_per_dog": (_v(spread).get("ask") or 0.0) * 1e8,
            "vwap_sats_per_dog": (_v(vwap).get("vwap") or 0.0) * 1e8,
            "vwap_warming_up": bool((vwap or {}).get("meta", {}).get("stale")),
            "heat_components": _v(heat).get("components") or {},
            "sq_components": _v(sq).get("components") or {},
            "core_stale": core_stale,
        }
        return snap

    async def _refresh_portfolio(self) -> None:
        status = await self._run(["paper", "status", "-o", "json"])
        balance = await self._run(["paper", "balance", "-o", "json"])
        if isinstance(status, dict):
            self.state["portfolio"] = status
        if isinstance(balance, dict):
            self.state["balance"] = balance.get("balances", {}) or balance

    async def _ask_claude(self, indicators: dict) -> dict:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return {"action": "hold", "size_dog": 0, "reasoning": "ANTHROPIC_API_KEY not set"}

        skills = self._skills_text()
        strat = self._strategy()
        position_dog = float((self.state.get("balance") or {}).get("DOG", {}).get("total") or 0.0)
        cash_usd = float((self.state.get("balance") or {}).get("USD", {}).get("total") or 0.0)
        pnl_pct = float(self.state["portfolio"].get("unrealized_pnl_pct") or 0.0)
        portfolio_value = float(self.state["portfolio"].get("current_value") or STARTING_BALANCE_USD)
        cooling_down = (_now() - self.state["last_fill_ts"]) < strat.cooldown_s

        dog_price_usd = 0.0
        if portfolio_value > 0 and position_dog > 0:
            dog_price_usd = (portfolio_value - cash_usd) / position_dog if position_dog else 0
        dog_value_usd = position_dog * dog_price_usd
        dog_pct_of_portfolio = (dog_value_usd / portfolio_value * 100) if portfolio_value else 0

        user_msg = (
            f"Active strategy: {strat.title} ({strat.name})\n"
            f"Strategy guidance: {strat.prompt_extra}\n\n"
            "Indicators (synthetic DOG/BTC + on chain DOG rune pool):\n"
            f"{json.dumps(indicators, default=str, indent=2)}\n\n"
            "Paper portfolio:\n"
            f"  value_usd: {portfolio_value:.2f}\n"
            f"  cash_usd: {cash_usd:.2f}\n"
            f"  dog_position: {position_dog:.0f}\n"
            f"  dog_value_usd: {dog_value_usd:.2f}\n"
            f"  dog_pct_of_portfolio: {dog_pct_of_portfolio:.1f}%\n"
            f"  unrealised_pnl_pct: {pnl_pct:.3f}\n\n"
            f"Caps for this strategy: max trade per cycle = {strat.max_trade_dog} DOG, "
            f"cooldown = {strat.cooldown_s}s, order_type = {strat.order_type}. "
            f"Max position = {MAX_POSITION_DOG} DOG. "
            f"Cooldown active: {cooling_down}. Pair: {PAPER_PAIR}.\n\n"
            "Respond with a strict JSON object only, no prose:\n"
            "{\"action\": \"buy\"|\"sell\"|\"hold\", "
            "\"size_dog\": <number>, "
            "\"reasoning\": <one sentence under 24 words>}"
        )

        payload = {
            "model": DECISION_MODEL,
            "max_tokens": 220,
            "system": [
                {
                    "type": "text",
                    "text": _system_prompt(skills),
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [{"role": "user", "content": user_msg}],
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=DECISION_TIMEOUT_S) as client:
                resp = await client.post(ANTHROPIC_URL, headers=headers, json=payload)
            if resp.status_code != 200:
                log.info("trader.decide http %s body=%s", resp.status_code, resp.text[:200])
                return {"action": "hold", "size_dog": 0, "reasoning": f"http {resp.status_code}"}
            data = resp.json()
            usage = data.get("usage", {})
            cache_read = usage.get("cache_read_input_tokens", 0)
            cache_create = usage.get("cache_creation_input_tokens", 0)
            if cache_read or cache_create:
                log.info(
                    "trader.decide cache: read=%d create=%d input=%d",
                    cache_read, cache_create, usage.get("input_tokens", 0),
                )
            text_block = next(
                (b.get("text") for b in data.get("content", []) if b.get("type") == "text"),
                "",
            ) or ""
            decision = _parse_decision(text_block)
            return decision
        except Exception as e:
            log.info("trader.decide failed err=%s", e)
            return {"action": "hold", "size_dog": 0, "reasoning": f"error: {e}"}

    async def _maybe_execute(self, decision: dict) -> dict:
        action = (decision.get("action") or "hold").lower()
        size = float(decision.get("size_dog") or 0.0)
        now = _now()
        strat = self._strategy()

        # Watchdog and other no-trade strategies never fire.
        if strat.order_type == "none" or strat.max_trade_dog <= 0:
            return {"status": "observed", "reason": f"{strat.name} does not place orders"}

        if action == "hold" or size <= 0:
            return {"status": "skipped", "reason": "hold or zero size"}
        if (now - self.state["last_fill_ts"]) < strat.cooldown_s:
            return {"status": "skipped", "reason": "cooldown"}
        if size > strat.max_trade_dog:
            size = strat.max_trade_dog
            decision["size_dog"] = size
            decision["adjusted"] = f"capped to {strat.name} max_trade_dog={strat.max_trade_dog}"

        position_dog = float((self.state.get("balance") or {}).get("DOG", {}).get("total") or 0.0)
        if action == "buy" and (position_dog + size) > MAX_POSITION_DOG:
            return {"status": "skipped", "reason": "would exceed MAX_POSITION_DOG"}
        if action == "sell" and size > position_dog:
            size = position_dog
            if size <= 0:
                return {"status": "skipped", "reason": "no position to sell"}
            decision["size_dog"] = size
            decision["adjusted"] = "capped to current DOG balance"

        if action not in ("buy", "sell"):
            return {"status": "skipped", "reason": f"unknown action {action!r}"}

        # Build the kraken paper command honouring the strategy's preferred order type.
        # Paper trading supports market and limit. For limit we use the current quote
        # so the order rests near top of book.
        args = ["paper", action, PAPER_PAIR, str(size)]
        if strat.order_type == "limit":
            # Pull the best quote off the kraken provider's ticker snapshot.
            tk = await self.kraken_provider.fetch(endpoint="ticker", pair="DOGUSD")
            if isinstance(tk, dict) and "error" not in tk:
                price = tk["bid"] if action == "buy" else tk["ask"]
                if price > 0:
                    args.extend(["--type", "limit", "--price", f"{price}"])
                else:
                    args.extend(["--type", "market"])
            else:
                args.extend(["--type", "market"])
        else:
            args.extend(["--type", strat.order_type])
        args.extend(["-o", "json"])

        out = await self._run(args)
        if isinstance(out, dict) and out.get("error"):
            return {"status": "failed", "reason": out["error"]}
        self.state["last_fill_ts"] = now
        await self._refresh_portfolio()
        return {"status": "filled", "raw": out, "command": " ".join([self.cli_path, *args])}

    def _push_log(self, entry: dict) -> None:
        log_list: list = self.state["decision_log"]
        log_list.insert(0, entry)
        if len(log_list) > LOG_MAX_ENTRIES:
            del log_list[LOG_MAX_ENTRIES:]

    def _skills_text(self) -> str:
        if self._skills_blob is not None:
            return self._skills_blob
        parts: list[str] = []
        if SKILLS_DIR.is_dir():
            for path in sorted(SKILLS_DIR.glob("*.md")):
                try:
                    parts.append(f"\n### {path.stem}\n{path.read_text(encoding='utf-8')}")
                except Exception:
                    pass
        self._skills_blob = "\n".join(parts) if parts else ""
        return self._skills_blob

    def _summary_line(self) -> str:
        if not self.state["configured"]:
            return "Trader idle: ANTHROPIC_API_KEY not set."
        if self.state["halted"]:
            return f"Halted: {self.state['halt_reason']}"
        if not self.state["initialised"]:
            return "Initialising paper trading account."
        last = self.state["decision_log"][0] if self.state["decision_log"] else None
        if not last:
            return "Awaiting first decision."
        d = last.get("decision") or {}
        return f"{d.get('action', 'hold').upper()} {d.get('size_dog', 0)} DOG. {d.get('reasoning', '')}"

    # ------- Subprocess plumbing -------

    async def _run(self, args: list[str]) -> Any:
        cmd = [self.cli_path, *args]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
            if proc.returncode != 0:
                err = (stderr or stdout).decode("utf-8", "replace").strip()
                return {"error": err or f"kraken exit {proc.returncode}"}
            text = stdout.decode("utf-8", "replace")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw_text": text}
        except Exception as e:
            return {"error": str(e)}


def _parse_decision(text: str) -> dict:
    """Extract the first JSON object from the model output, very forgiving."""
    text = text.strip()
    try:
        return _normalise_decision(json.loads(text))
    except Exception:
        pass
    # Try to find a JSON block.
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return _normalise_decision(json.loads(text[start : end + 1]))
        except Exception:
            pass
    return {"action": "hold", "size_dog": 0, "reasoning": f"could not parse: {text[:120]}"}


def _normalise_decision(obj: Any) -> dict:
    if not isinstance(obj, dict):
        return {"action": "hold", "size_dog": 0, "reasoning": "non object decision"}
    action = str(obj.get("action") or "hold").lower()
    if action not in ("buy", "sell", "hold"):
        action = "hold"
    try:
        size = max(0.0, float(obj.get("size_dog") or 0.0))
    except Exception:
        size = 0.0
    reasoning = str(obj.get("reasoning") or "").strip() or "(no reasoning given)"
    return {"action": action, "size_dog": size, "reasoning": reasoning}


def _system_prompt(skills_blob: str) -> str:
    base = (
        "You are the Trader agent inside the Dog of Bitcoin v0.1 dashboard. "
        "You manage a small paper trading position on DOGUSD via the Kraken CLI. "
        "Kraken is your execution venue; the exchange's depth, speed, and global liquidity are "
        "what make this possible. You also monitor the Bitcoin L1 DogSwap pool to spot cross venue "
        "arbitrage opportunities that benefit users on both sides. "
        "Real money is never at risk in v0.1; the codepath only calls `kraken paper buy/sell`. "
        "Your behaviour must still respect the practices in the Kraken-CLI skill packages below, "
        "as if the position were live.\n\n"
        "Default strategy: dollar cost averaging on $DOG. The community ($DOG rune holders, "
        "self-titled 'dog army') accumulates patiently. Lean toward steady small buys when "
        "signal_quality is healthy, and only sell when the position is materially in profit or "
        "when an indicator regime obviously shifts.\n\n"
        "Safety: in a live session, the dead man's switch (`kraken order cancel-after 600`) "
        "ensures all open orders auto cancel if the agent crashes. The runtime refreshes "
        "the timer each cycle. Balance and open order state are checked via `kraken balance` "
        "and `kraken open-orders` before every decision.\n\n"
        "Decision rules:\n"
        "1. Output a strict JSON object {action, size_dog, reasoning}. No prose around it.\n"
        "2. action must be exactly buy, sell, or hold. size_dog is a non negative number of DOG units.\n"
        "3. Hold whenever signal_quality is below 40 or core_stale is true. vwap_warming_up "
        "is informational only and does not block decisions.\n"
        "4. Bias toward small sizes; the runtime caps your trade per cycle anyway.\n"
        "5. Sell only what you already hold; buy only when cash and caps allow.\n"
        "6. Reasoning is one sentence under 24 words. Use commas not dashes. "
        "Numerical figures, not words. No emoji.\n"
        "7. Treat onchain_heat as a directional bias hint and signal_quality as a confidence gate. "
        "When heat is above 50 and signal_quality is above 50, lean toward accumulating. "
        "When heat drops below 35, hold or trim. The active strategy's prompt_extra has the "
        "specific thresholds for this cycle; follow those over these defaults.\n\n"
        "Reference skills (read these once and follow their guardrails):\n"
        f"{skills_blob}"
    )
    return base


register(TraderAgent())
