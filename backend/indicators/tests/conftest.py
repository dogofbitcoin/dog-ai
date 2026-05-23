"""Indicator test fixtures.

A fake indicator context that returns canned provider payloads. Lets each
indicator test exercise pure logic against deterministic inputs.
"""

from __future__ import annotations

import pytest


class FakeContext:
    def __init__(self, now_ts: int, payloads: dict):
        self.now_ts = now_ts
        self._payloads = payloads

    async def fetch(self, name: str, **kwargs):
        key_specific = (name, kwargs.get("endpoint"))
        if key_specific in self._payloads:
            return self._payloads[key_specific]
        if name in self._payloads:
            return self._payloads[name]
        return {"error": f"no fake payload for {name} {kwargs}"}


@pytest.fixture
def fake_ctx():
    def make(now_ts: int, payloads: dict) -> FakeContext:
        return FakeContext(now_ts=now_ts, payloads=payloads)

    return make
