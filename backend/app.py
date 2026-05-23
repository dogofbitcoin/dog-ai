"""FastAPI entry for Dog of Bitcoin v0.1.

Routes:
  GET  /health                       liveness
  GET  /health/providers             per provider health
  GET  /providers                    list registered providers
  GET  /providers/{name}/snapshot    raw fetch from one provider
  GET  /indicators                   list registered indicators
  GET  /indicators/{name}            computed indicator envelope
  GET  /kraken/dry-run               build a dry run kraken CLI command string

The dashboard polls `/indicators` and `/health/providers` on a fixed cadence.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Importing the packages triggers self registration.
from . import agents as _agt  # noqa: E402
from . import indicators as _ind  # noqa: E402
from . import providers as _prov  # noqa: E402
from .log import log  # noqa: E402
from .providers.kraken import KrakenProvider  # noqa: E402

app = FastAPI(title="Dog of Bitcoin", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/health/providers")
async def health_providers() -> dict:
    out: list[dict[str, Any]] = []
    for p in _prov.all_providers():
        h = await p.health()
        out.append({"name": p.name, "kind": p.kind, **h})
    overall = all(item.get("ok") for item in out) if out else False
    return {"ok": overall, "providers": out}


@app.get("/providers")
async def list_providers() -> dict:
    return {
        "providers": [
            {"name": p.name, "kind": p.kind} for p in _prov.all_providers()
        ]
    }


@app.get("/providers/{name}/snapshot")
async def provider_snapshot(name: str) -> dict:
    try:
        p = _prov.get(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return await p.fetch()


@app.get("/indicators")
async def list_indicators() -> dict:
    out: list[dict[str, Any]] = []
    for ind in _ind.all_indicators():
        ctx = _ind.make_context(ind)
        env = await ind.compute(ctx)
        out.append({
            "name": ind.name,
            "inputs": ind.inputs,
            "window_seconds": ind.window_seconds,
            "envelope": env,
        })
    return {"indicators": out}


@app.get("/indicators/{name}")
async def get_indicator(name: str) -> dict:
    try:
        ind = _ind.get(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    ctx = _ind.make_context(ind)
    return {
        "name": ind.name,
        "inputs": ind.inputs,
        "window_seconds": ind.window_seconds,
        "envelope": await ind.compute(ctx),
    }


@app.get("/agents")
async def list_agents() -> dict:
    out: list[dict[str, Any]] = []
    for ag in _agt.all_agents():
        ctx = _agt.make_context(ag)
        env = await ag.decide(ctx)
        out.append({"name": ag.name, "inputs": ag.inputs, "envelope": env})
    return {"agents": out}


@app.get("/agents/{name}")
async def get_agent(name: str) -> dict:
    try:
        ag = _agt.get(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    ctx = _agt.make_context(ag)
    return {"name": ag.name, "inputs": ag.inputs, "envelope": await ag.decide(ctx)}


@app.get("/agents/trader/strategies")
async def list_trader_strategies() -> dict:
    from .agents.strategies import list_strategies
    from .agents.trader import TraderAgent
    trader = _agt.get("trader")
    active = trader.state["strategy"] if isinstance(trader, TraderAgent) else None
    return {"active": active, "strategies": list_strategies()}


@app.post("/agents/trader/strategy")
async def set_trader_strategy(name: str = Query(..., min_length=1)) -> dict:
    from .agents.trader import TraderAgent
    trader = _agt.get("trader")
    if not isinstance(trader, TraderAgent):
        raise HTTPException(status_code=500, detail="trader agent missing")
    ok = trader.set_strategy(name)
    if not ok:
        from .agents.strategies import list_strategies
        raise HTTPException(
            status_code=400,
            detail={"error": f"unknown strategy {name!r}", "available": [s["name"] for s in list_strategies()]},
        )
    return {"active": trader.state["strategy"]}


@app.get("/kraken/dry-run")
async def kraken_dry_run(
    side: str = Query(..., pattern="^(buy|sell)$"),
    volume: float = Query(..., gt=0),
    price: float | None = Query(None, gt=0),
    pair: str | None = None,
    order_type: str = Query("limit", pattern="^(limit|market)$"),
) -> dict:
    """Build the kraken CLI string the operator should run. Never executes.
    This is the canonical v0.1 contract for surfacing trade ideas."""
    p = _prov.get("kraken")
    if not isinstance(p, KrakenProvider):
        raise HTTPException(status_code=500, detail="kraken provider missing")
    cmd = p.build_action_command(
        side=side,
        volume=volume,
        pair=pair,
        price=price,
        order_type=order_type,
        validate=True,
    )
    return {"command": cmd, "note": "v0.1 is read only; copy this and run it yourself."}


_trader_task: Any = None


async def _trader_loop() -> None:
    from .agents.trader import DECISION_CADENCE_S, TraderAgent
    trader = _agt.get("trader")
    assert isinstance(trader, TraderAgent)
    while True:
        try:
            await trader.cycle(ctx_factory=lambda: _agt.make_context(trader))
        except Exception as e:
            log.warning("trader cycle errored: %s", e)
        await asyncio.sleep(DECISION_CADENCE_S)


@app.on_event("startup")
async def _startup() -> None:
    global _trader_task
    log.info(
        "dog of bitcoin backend up; providers=%s indicators=%s agents=%s",
        [p.name for p in _prov.all_providers()],
        [i.name for i in _ind.all_indicators()],
        [a.name for a in _agt.all_agents()],
    )
    if os.getenv("TRADER_DISABLED") == "1":
        log.info("trader loop disabled via TRADER_DISABLED=1")
        return
    _trader_task = asyncio.create_task(_trader_loop())


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _trader_task
    if _trader_task is not None:
        _trader_task.cancel()
        try:
            await _trader_task
        except (asyncio.CancelledError, Exception):
            pass
