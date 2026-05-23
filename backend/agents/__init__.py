"""Agent registry.

Agents self register at import time. Importing this module triggers the imports
of every agent implementation so the registry is populated before the first
consumer call.
"""

from __future__ import annotations

import time

from .base import Agent, AgentContext

_REGISTRY: dict[str, Agent] = {}


def register(agent: Agent) -> None:
    if not agent.name:
        raise ValueError("Agent.name must be set")
    if agent.name in _REGISTRY:
        raise ValueError(f"Agent {agent.name!r} already registered")
    _REGISTRY[agent.name] = agent


def get(name: str) -> Agent:
    if name not in _REGISTRY:
        raise KeyError(f"Agent {name!r} not registered. Known: {list(_REGISTRY)}")
    return _REGISTRY[name]


def all_agents() -> list[Agent]:
    return list(_REGISTRY.values())


def make_context(agent: Agent, now_ts: int | None = None) -> AgentContext:
    return AgentContext(
        allowed_inputs=list(agent.inputs),
        now_ts=now_ts if now_ts is not None else int(time.time()),
    )


# Import implementations so they self register. Alphabetical.
from . import alpha  # noqa: E402, F401
from . import general  # noqa: E402, F401
