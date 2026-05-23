# Providers

A **provider** is any module that supplies data to the agents. Each provider lives in its own file under `backend/providers/` and conforms to a single interface so agents and indicators stay decoupled from the source.

v0.1 ships with one on-chain provider (DotSwap) and one market provider (Kraken CLI). Anything added later — a second on-chain source, a sentiment feed, a mempool watcher — drops into the same directory and registers itself the same way.

## Directory layout

```
backend/providers/
├── __init__.py          # registry + base class
├── base.py              # Provider ABC
├── dotswap.py           # $DOG Rune on-chain data via DotSwap L1
├── kraken.py            # Kraken CLI wrapper for market data
└── README.md            # one-line summary of each provider
```

## The Provider interface

Every provider subclasses `Provider` from `backend/providers/base.py`. The contract is intentionally minimal so new sources can be added without touching the agents.

```python
from abc import ABC, abstractmethod

class Provider(ABC):
    name: str           # unique key, e.g. "dotswap", "kraken"
    kind: str           # "onchain" | "market" | "sentiment" | "other"

    @abstractmethod
    async def fetch(self, **kwargs) -> dict:
        """Return a normalized payload. Never raise — return {"error": "..."} instead."""

    @abstractmethod
    async def health(self) -> dict:
        """Return {"ok": bool, "latency_ms": int, "note": str}."""
```

Two rules that keep the system stable:

1. **Never raise out of a provider.** Agents poll providers on a clock; an exception silently drops the panel. Wrap the call site and return `{"error": "..."}` so the UI can render a graceful state.
2. **Return normalized shapes.** The agents do not care which provider produced the data. If two providers describe a price, they both return `{"price": float, "ts": int, "source": str}`.

## Registering a provider

Providers register themselves at import time via the registry in `backend/providers/__init__.py`. No central wiring file to edit.

```python
# backend/providers/dotswap.py
from .base import Provider
from . import register

class DotSwapProvider(Provider):
    name = "dotswap"
    kind = "onchain"
    ...

register(DotSwapProvider())
```

Agents pull by name:

```python
from backend.providers import get
dotswap = get("dotswap")
data = await dotswap.fetch(rune="DOG")
```

## DotSwap (v0.1)

DotSwap is the sole on-chain source for $DOG Rune data in v0.1. It is L1-native and purpose-built for Runes, which matches what the agents need.

- **Endpoints:** configured in `backend/providers/dotswap.py` from env vars (`DOTSWAP_API_BASE`, `DOTSWAP_API_KEY`).
- **What it returns:** floor, volume, holder count, recent fills, depth at the top of book. Normalized into the standard on-chain payload.
- **Caching:** 60-second in-memory cache on the fetch path to avoid hammering the endpoint during demos. Set `DOTSWAP_CACHE_TTL=0` to disable.

If DotSwap is down the provider returns `{"error": "dotswap unreachable"}` and the on-chain panel renders a muted state. There is no fallback chain in v0.1 by design — keeping a single source means the data story stays honest. A second source can be added later by writing a new provider file and registering it; the agents do not need to change.

## Kraken (v0.1)

The Kraken provider wraps the Kraken CLI installed on the AWS box. It is read-only in v0.1 — no orders are placed. All operator-driven actions are emitted as **dry-run** CLI strings for the user to copy or execute manually.

- **CLI path:** `KRAKEN_CLI_PATH` env var, defaults to `kraken`.
- **Pair:** defaults to `DOGBTC`. Override with `KRAKEN_PAIR`.
- **Output:** ticker, order book snapshot (top 10), recent trades, spread. Normalized into the standard market payload.

## Adding a new provider

1. Create `backend/providers/<name>.py`.
2. Subclass `Provider`, set `name` and `kind`, implement `fetch` and `health`.
3. Call `register(<YourProvider>())` at the bottom of the file.
4. Add a one-line entry to `backend/providers/README.md`.
5. Reference it from any indicator or agent via `get("<name>")`.

That is the whole onboarding. The agents and the indicator registry pick it up on next start with no changes elsewhere.

## Configuration

All provider config lives in environment variables, never hardcoded. The canonical `.env.example` in the repo root lists every variable the providers read. Add new variables there when you add a new provider so others know what to set.

## Testing a provider

Each provider ships with a `health()` method that the `/health` API route surfaces. From the AWS box:

```bash
curl http://localhost:8000/health/providers
```

Returns a list of `{name, ok, latency_ms, note}`. Use this as the first check when a panel goes dark.
