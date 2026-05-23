# Indicators

An **indicator** is a small, focused computation that turns raw provider data into a single signal the agents can speak to. Spread, VWAP, signal quality, on-chain heat — each one is its own file, each one self-registers, and each one is independently testable.

Indicators do not call agents and agents do not reach into indicator internals. The agents ask the registry for a named indicator and read its output. This is what lets the project add a new indicator in v0.2 without touching anything that already works.

## Directory layout

```
backend/indicators/
├── __init__.py          # registry + base class
├── base.py              # Indicator ABC
├── spread.py            # bid/ask spread, normalized
├── vwap.py              # rolling volume-weighted average price
├── signal_quality.py    # composite freshness/depth/agreement score
├── onchain_heat.py      # $DOG Rune activity intensity
└── README.md            # one-line summary of each indicator
```

## The Indicator interface

Every indicator subclasses `Indicator` from `backend/indicators/base.py`.

```python
from abc import ABC, abstractmethod

class Indicator(ABC):
    name: str              # unique key, e.g. "spread", "vwap"
    inputs: list[str]      # provider names this indicator reads from
    window_seconds: int    # rolling window, or 0 for snapshot

    @abstractmethod
    async def compute(self, ctx) -> dict:
        """Return {"value": ..., "ts": int, "meta": {...}}."""
```

The `ctx` object gives the indicator typed access to the providers it declared in `inputs`. An indicator that did not declare a provider in `inputs` cannot reach it. This keeps dependencies visible at a glance.

## Registering an indicator

Same pattern as providers — self-registration at import time.

```python
# backend/indicators/spread.py
from .base import Indicator
from . import register

class SpreadIndicator(Indicator):
    name = "spread"
    inputs = ["kraken"]
    window_seconds = 0
    ...

register(SpreadIndicator())
```

Agents pull by name:

```python
from backend.indicators import get
spread = await get("spread").compute(ctx)
```

## v0.1 indicators

### `spread`
Source: Kraken. Returns top-of-book bid/ask spread in basis points plus the raw quotes. Snapshot indicator, no window.

### `vwap`
Source: Kraken. Rolling 5-minute volume-weighted average price. Window configurable via `VWAP_WINDOW_SECONDS`.

### `signal_quality`
Source: composite (Kraken + DotSwap). A 0-100 score combining data freshness, order book depth, and cross-source agreement. Designed for the Alpha agent to gate when to speak with confidence vs hedge.

### `onchain_heat`
Source: DotSwap. A 0-100 score combining recent fill rate, holder delta, and volume velocity on the $DOG Rune. The General agent uses this to push or hold a directional stance.

Each one lives in its own file. None of them know about each other.

## Adding a new indicator

1. Create `backend/indicators/<name>.py`.
2. Subclass `Indicator`, set `name`, `inputs`, `window_seconds`, implement `compute`.
3. Call `register(<YourIndicator>())` at the bottom of the file.
4. Add a one-line entry to `backend/indicators/README.md`.
5. If an agent should consume it, reference it by name from the agent's prompt or logic — no central registration to edit.

## Output shape

Every indicator returns the same envelope:

```python
{
    "value": <number | dict | str>,   # the indicator-specific payload
    "ts": <int unix seconds>,         # when computed
    "meta": {
        "stale": <bool>,              # true if any input was older than window
        "sources": [<provider names>],
        "notes": <str | None>
    }
}
```

The frontend keys off `meta.stale` to render the muted state. Indicators that compute on a stale input should still return a value but flip `stale=True` — never silently drop.

## Windows and caching

Indicators with `window_seconds > 0` keep a small in-memory ring buffer. The buffer survives within a process but is not persisted. v0.1 makes no attempt at durable history — if the process restarts, windows refill over time. This is deliberate for v0.1; durable history is a v0.2 candidate (see `CHANGELOG.md` under Planned).

## Testing an indicator

Each indicator should ship with a `tests/test_<name>.py` that fakes the provider input and asserts the output envelope. Indicators must be pure functions of their declared inputs — if it needs the wall clock or randomness, inject it. This keeps the test suite deterministic.

## What indicators should not do

- Do not call agents.
- Do not write to disk.
- Do not log to stdout (use the project logger).
- Do not bypass the registry to reach a provider not declared in `inputs`.
- Do not produce different output shapes under different conditions — use `meta.stale` and `meta.notes`.

The whole point of the directory is that an indicator is a self-contained unit. If a new requirement breaks any of the above, it probably wants to be a new module, not a modification.
