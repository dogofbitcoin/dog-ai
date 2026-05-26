"""Optional LLM narration for agent reasoning.

Agent stance and confidence are always rule based and deterministic. The
prose reasoning can optionally be rewritten by Claude when `ANTHROPIC_API_KEY`
is set in the environment. If the call fails for any reason we fall back to
the base reasoning string. Behaviour never changes; only the wording does.

This keeps the agents testable while still letting the dashboard surface a
more readable narration when an API key is available.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from ..log import log

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_MODEL = os.getenv("DOB_NARRATION_MODEL", "claude-haiku-4-5-20251001")
_TIMEOUT_S = float(os.getenv("DOB_NARRATION_TIMEOUT", "4.0"))
_ENABLED = bool(os.getenv("ANTHROPIC_API_KEY"))


def _system_prompt(agent_name: str) -> str:
    # No dashes in prose per project style rule. Plain, short, factual.
    return (
        "You are rewriting one short reasoning line for the "
        f"{agent_name} agent in the Dog of Bitcoin dashboard. "
        "Keep it to one sentence under 24 words. Use commas, not dashes. "
        "Numerical figures, not words. No emoji. State what the numbers show. "
        "Do not invent values. Do not add a sign off or preamble."
    )


async def maybe_narrate(
    agent_name: str,
    stance: str,
    base_reasoning: str,
    extras: dict[str, Any],
) -> str:
    """Return either the LLM rewrite or the original base_reasoning."""
    if not _ENABLED:
        return base_reasoning
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return base_reasoning
    payload = {
        "model": _MODEL,
        "max_tokens": 120,
        "system": [
            {
                "type": "text",
                "text": _system_prompt(agent_name),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Stance: {stance}.\n"
                    f"Base reasoning: {base_reasoning}\n"
                    f"Numbers (do not invent others): {extras}"
                ),
            }
        ],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(_ANTHROPIC_URL, headers=headers, json=payload)
        if resp.status_code != 200:
            log.info("narrate http %s; falling back", resp.status_code)
            return base_reasoning
        data = resp.json()
        # The content is a list of blocks; we want the first text block.
        for block in data.get("content", []):
            if block.get("type") == "text":
                text = (block.get("text") or "").strip()
                if text:
                    return text
        return base_reasoning
    except Exception as e:
        log.info("narrate call failed err=%s; falling back", e)
        return base_reasoning
