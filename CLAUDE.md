# CLAUDE.md

Project conventions for Claude Code sessions on this repo. Read on session start.

## What this is

A small read only dashboard for the $DOG Rune. Backend in Python (FastAPI), frontend in React (Vite). Providers, indicators, and agents are decoupled and self register. See `docs/PROVIDERS.md` and `docs/INDICATORS.md` for the contracts.

## Style rules (these are non negotiable in committed code and docs)

1. No dashes in prose. Use commas, semicolons, or rewrite. Applies to README, doc comments, PR descriptions, commit messages, and any user facing copy. Hyphens in identifiers, CLI flags, and code are fine.
2. Numerical figures, not words. Write "5 providers" not "five providers", "20%" not "twenty percent".
3. No emoji in code, commits, or docs.
4. Python 3.11+. Format with `black` (line length 100). Lint with `ruff`. Type hints on public functions and on provider and indicator interfaces.
5. JavaScript: function components only, no class components. Hooks in `frontend/src/hooks/`, one file per hook.

## Architecture rules

1. Providers never raise out. On failure they return `{"error": "..."}`. The UI renders a muted state.
2. Providers and indicators self register at import time via the registry in `backend/providers/__init__.py` and `backend/indicators/__init__.py`. No central wiring file to edit.
3. Indicators are pure functions of their declared `inputs`. Inject clocks and randomness so tests stay deterministic.
4. v0.1 is read only on the trading side. The Kraken provider does not place orders. Operator actions are emitted as dry run CLI strings.
5. All config in env vars. The canonical list lives in `.env.example`. Add new variables there when you add a new consumer.

## Branch model

- `main` is protected. Curated, reviewed, releasable. Merges via PR only.
- `develop` is the integration branch for the next release.
- `claude-aws` is the autonomous branch from the AWS Claude Code agent. The bot identity is `dog-of-bitcoin-bot <bot@dogofbitcoin.com>`. Direct push allowed on that branch only.
- `feature/<name>` for human contributor work. PR into `develop`.

The AWS agent commits only to `claude-aws`. Maintainers cherry pick or merge those into `develop` after review.

## Tests

- Backend tests live next to the module: `backend/providers/tests/`, `backend/indicators/tests/`.
- Frontend tests live next to the component: `frontend/src/components/__tests__/`.
- Tests must be deterministic. No network, no clock, no randomness. If a test flakes, that is a bug.
- New providers and indicators ship with at least one test that exercises the public interface.

## When something is wrong

Order of triage:
1. `curl http://localhost:8000/health/providers`
2. `journalctl -u dob-backend -n 100` (AWS) or backend stdout (local)
3. Browser console
4. `pytest backend/providers/tests/` and `pytest backend/indicators/tests/`

If all four are clean and the dashboard still looks wrong, the bug is in an indicator or agent. Pull the relevant module test and run it in isolation.
