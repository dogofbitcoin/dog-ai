"""Agent base class.

An agent reads indicators and produces a single stance with a short rationale.
Agents do not call providers directly; they go through an AgentContext that
only exposes the indicators the agent declared in `inputs`.

Output envelope (every agent returns this shape):

    {
        "stance": <str>,              # agent specific label, e.g. "bullish"
        "confidence": <float 0-100>,  # how strongly the agent believes it
        "reasoning": <str>,           # one or two sentences
        "inputs_seen": [<indicator names>],
        "ts": <int unix seconds>,
        "meta": {
            "stale": <bool>,          # any input was stale or missing
            "notes": <str | None>,
        },
    }
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Agent(ABC):
    name: str
    inputs: list[str]  # indicator names this agent depends on

    @abstractmethod
    async def decide(self, ctx: "AgentContext") -> dict:
        """Return the standard agent envelope; see module docstring."""


class AgentContext:
    """Indicator access scoped to the agent's declared inputs."""

    def __init__(self, allowed_inputs: list[str], now_ts: int):
        from ..indicators import get as get_indicator
        from ..indicators import make_context as make_indicator_context

        self._allowed = set(allowed_inputs)
        self._get_indicator = get_indicator
        self._make_indicator_context = make_indicator_context
        self.now_ts = now_ts

    async def indicator(self, name: str) -> dict:
        if name not in self._allowed:
            raise PermissionError(
                f"Agent did not declare {name!r} in inputs; allowed={sorted(self._allowed)}"
            )
        ind = self._get_indicator(name)
        ictx = self._make_indicator_context(ind, now_ts=self.now_ts)
        return await ind.compute(ictx)
