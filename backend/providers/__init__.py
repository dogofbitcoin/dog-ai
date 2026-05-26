"""Provider registry.

Providers self register at import time via `register()`. Importing this module
triggers the imports of every provider implementation in the package so the
registry is populated before the first consumer call.
"""

from __future__ import annotations

from .base import Provider

_REGISTRY: dict[str, Provider] = {}


def register(provider: Provider) -> None:
    if not provider.name:
        raise ValueError("Provider.name must be set")
    if provider.name in _REGISTRY:
        raise ValueError(f"Provider {provider.name!r} already registered")
    _REGISTRY[provider.name] = provider


def get(name: str) -> Provider:
    if name not in _REGISTRY:
        raise KeyError(f"Provider {name!r} not registered. Known: {list(_REGISTRY)}")
    return _REGISTRY[name]


def all_providers() -> list[Provider]:
    return list(_REGISTRY.values())


# Import implementations so they self register.
# Order is alphabetical, not load bearing.
from . import dotswap  # noqa: E402, F401
from . import kraken  # noqa: E402, F401
from . import treasury  # noqa: E402, F401
