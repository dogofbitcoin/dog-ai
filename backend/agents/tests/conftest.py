"""Agent test fixtures.

A fake context that returns canned indicator envelopes so each agent test
exercises pure stance logic.
"""

from __future__ import annotations

import pytest


class FakeAgentContext:
    def __init__(self, now_ts: int, envelopes: dict):
        self.now_ts = now_ts
        self._envelopes = envelopes

    async def indicator(self, name: str):
        if name not in self._envelopes:
            return {
                "value": None,
                "ts": self.now_ts,
                "meta": {"stale": True, "sources": [], "notes": f"no fake for {name}"},
            }
        return self._envelopes[name]


@pytest.fixture
def fake_agent_ctx():
    def make(now_ts: int, envelopes: dict) -> FakeAgentContext:
        return FakeAgentContext(now_ts=now_ts, envelopes=envelopes)

    return make
