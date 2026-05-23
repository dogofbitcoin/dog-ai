"""Provider base class.

A provider supplies data to indicators and agents. The contract is intentionally
minimal so new sources slot in without touching the consumers.

Rules:
  1. Never raise. On failure return {"error": "..."}.
  2. Return normalized shapes. Consumers should not know which provider
     produced a given payload.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Provider(ABC):
    name: str
    kind: str  # "onchain" | "market" | "sentiment" | "other"

    @abstractmethod
    async def fetch(self, **kwargs: Any) -> dict:
        """Return a normalized payload. Never raise; return {"error": "..."} instead."""

    @abstractmethod
    async def health(self) -> dict:
        """Return {"ok": bool, "latency_ms": int, "note": str}."""
