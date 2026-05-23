"""Kraken provider tests.

Tests stub the CLI by replacing `_run`. No subprocess and no network.
"""

from __future__ import annotations

import pytest

from backend.providers.kraken import KrakenProvider


def _ticker_response(pair_key: str, bid: str, ask: str, last: str) -> dict:
    return {
        pair_key: {
            "a": [ask, "1", "1.000"],
            "b": [bid, "1", "1.000"],
            "c": [last, "0.00"],
            "h": [last, last],
            "l": [last, last],
            "o": last,
            "p": [last, last],
            "t": [0, 0],
            "v": ["0", "0"],
        }
    }


@pytest.mark.asyncio
async def test_ticker_direct_pair_parses_bid_ask(monkeypatch):
    p = KrakenProvider()
    monkeypatch.setattr(
        p, "_run", _async(lambda *a, **kw: _ticker_response("DOGUSD", "0.000715", "0.000718", "0.000718"))
    )
    out = await p.fetch(endpoint="ticker", pair="DOGUSD")
    assert out["bid"] == 0.000715
    assert out["ask"] == 0.000718
    assert out["pair"] == "DOGUSD"
    assert out["synthetic"] is False


@pytest.mark.asyncio
async def test_synthetic_dogbtc_combines_dog_and_btc(monkeypatch):
    p = KrakenProvider()

    async def fake_run(args):
        if args[:2] == ["ticker", "DOGUSD"]:
            return _ticker_response("DOGUSD", "0.0007", "0.00072", "0.00071")
        if args[:2] == ["ticker", "XBTUSD"]:
            return _ticker_response("XXBTZUSD", "70000", "70100", "70050")
        raise AssertionError(f"unexpected args {args}")

    monkeypatch.setattr(p, "_run", fake_run)
    out = await p.fetch(endpoint="ticker", pair="DOGBTC")
    assert out["synthetic"] is True
    assert out["bid"] == pytest.approx(0.0007 / 70100, rel=1e-9)
    assert out["ask"] == pytest.approx(0.00072 / 70000, rel=1e-9)


@pytest.mark.asyncio
async def test_fetch_returns_error_envelope_on_cli_failure(monkeypatch):
    p = KrakenProvider()

    async def boom(_args):
        raise RuntimeError("cli broke")

    monkeypatch.setattr(p, "_run", boom)
    out = await p.fetch(endpoint="ticker", pair="DOGUSD")
    assert "error" in out
    assert "cli broke" in out["error"]


def test_dry_run_substitutes_synthetic_for_underlying():
    p = KrakenProvider()
    cmd = p.build_action_command(side="buy", volume=10000, pair="DOGBTC", price=0.0007)
    assert "DOGUSD" in cmd
    assert "DOGBTC" not in cmd
    assert "--validate" in cmd
    assert cmd.startswith(p.cli_path)


def _async(fn):
    async def _wrapped(*args, **kwargs):
        return fn(*args, **kwargs)

    return _wrapped
