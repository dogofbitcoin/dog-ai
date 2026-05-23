"""Indicator base class.

An indicator is a small focused computation that turns provider data into a
single named signal. Indicators are pure functions of their declared `inputs`.
Inject the clock and any randomness so tests stay deterministic.

Output envelope (every indicator returns this shape):

    {
        "value": <number | dict | str>,
        "ts": <int unix seconds>,
        "meta": {
            "stale": <bool>,
            "sources": [<provider names>],
            "notes": <str | None>,
        },
    }
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Indicator(ABC):
    name: str
    inputs: list[str]
    window_seconds: int = 0

    @abstractmethod
    async def compute(self, ctx: "IndicatorContext") -> dict:
        """Return the standard envelope; see module docstring."""


class IndicatorContext:
    """Typed access to providers an indicator declared in `inputs`.

    Construction is the registry's job. Callers should not instantiate this
    directly. The context refuses to hand out providers the indicator did not
    declare; that keeps dependency graphs visible.
    """

    def __init__(self, allowed_providers: list[str], now_ts: int):
        from ..providers import get as get_provider

        self._allowed = set(allowed_providers)
        self._get_provider = get_provider
        self.now_ts = now_ts

    def provider(self, name: str):
        if name not in self._allowed:
            raise PermissionError(
                f"Indicator did not declare {name!r} in inputs; allowed={sorted(self._allowed)}"
            )
        return self._get_provider(name)

    async def fetch(self, name: str, **kwargs: Any) -> dict:
        return await self.provider(name).fetch(**kwargs)
