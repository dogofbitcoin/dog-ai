"""Indicator registry.

Indicators self register at import time. Importing this module triggers the
imports of every indicator implementation so the registry is populated before
the first consumer call.
"""

from __future__ import annotations

import time

from .base import Indicator, IndicatorContext

_REGISTRY: dict[str, Indicator] = {}


def register(indicator: Indicator) -> None:
    if not indicator.name:
        raise ValueError("Indicator.name must be set")
    if indicator.name in _REGISTRY:
        raise ValueError(f"Indicator {indicator.name!r} already registered")
    _REGISTRY[indicator.name] = indicator


def get(name: str) -> Indicator:
    if name not in _REGISTRY:
        raise KeyError(f"Indicator {name!r} not registered. Known: {list(_REGISTRY)}")
    return _REGISTRY[name]


def all_indicators() -> list[Indicator]:
    return list(_REGISTRY.values())


def make_context(indicator: Indicator, now_ts: int | None = None) -> IndicatorContext:
    return IndicatorContext(
        allowed_providers=list(indicator.inputs),
        now_ts=now_ts if now_ts is not None else int(time.time()),
    )


# Import implementations so they self register. Alphabetical.
from . import arb_spread  # noqa: E402, F401
from . import onchain_heat  # noqa: E402, F401
from . import signal_quality  # noqa: E402, F401
from . import spread  # noqa: E402, F401
from . import vwap  # noqa: E402, F401
