# DOG Ai

The agent stack for DOG on Bitcoin L1. Born from Kraken's Agent Zero, the moment the exchange reached its tentacles toward the base layer.

> **v0.1.0 Release The Kraken**
> Kraken Agent Zero submission, deadline 2026-05-27.
> Live dashboard: `http://98.87.230.156:5173`

## What this is

A public dashboard with 4 autonomous AI characters watching the DOG Rune across DotSwap (Bitcoin L1) and Kraken (centralized exchange). Dog of Bitcoin is the main character. He runs on paper, picks one of 4 strategies, and emits Kraken CLI commands. The 3 supporting agents narrate the regime around him.

```
agent dog of bitcoin     main character        strategy + paper trader
agent kraken             exchange specialist   CLI surface + skill picker
agent alpha              data confidence       signal quality narrator
agent general ghost      directional           bullish, neutral, bearish
```

## Stack at a glance

| Layer | Tech | Notes |
|---|---|---|
| Backend | FastAPI, Python 3.11, uvicorn | port 8000, systemd unit `dob-backend` |
| Frontend | React, Vite | port 5173, systemd unit `dob-frontend` |
| Exchange | Kraken CLI 0.3.2 | paper mode in v0.1, 8 SKILL files mirrored from `krakenfx/kraken-cli` |
| On chain | Nexus protocol | reads the DotSwap DOG, BTC pool |
| Agents | autonomous, self registering | each character runs on its own loop, reads indicators, picks an action |

## Quick start

```
git clone git@github.com:dogofbitcoin/dog-ai.git
cd dog-ai
cp .env.example .env
# fill in ANTHROPIC_API_KEY, NEXUS_URL, NEXUS_API_KEY

python3.11 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8000 &

cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open `http://localhost:5173`. See `docs/RUNNING.md` for the long version.

## Branch model

- `main` protected, curated releases
- `develop` integration branch, default for collaborators
- `claude-aws` autonomous AWS Claude implementer branch
- `feature/<name>` for human contributor work

See `docs/COLLABORATION.md` for the two Claude workflow (desktop Claude owns the visual spec from screenshots, AWS Claude implements to spec without image access).

## Documentation map

| Document | Covers |
|---|---|
| `CLAUDE.md` | Style rules, conventions for any Claude session on this repo |
| `docs/UI_SPEC.md` | Visual contract, layout, color tokens, components, motion |
| `docs/COLLABORATION.md` | Two Claude workflow, file ownership, branch rules |
| `docs/reference/README.md` | Screenshot drop folder + scene tag naming |
| `docs/PROVIDERS.md` | Provider interface contract |
| `docs/INDICATORS.md` | Indicator interface contract |
| `docs/CONTRIBUTING.md` | Tests required, no live trading in v0.1 |
| `docs/RUNNING.md` | Full local setup walkthrough |
| `docs/kraken-skills/` | 8 SKILL.md files mirrored from `krakenfx/kraken-cli`, MIT, attribution in `LICENSE.kraken-cli` |

## Hard constraints in v0.1

1. No live trading. Dog of Bitcoin uses `kraken paper buy` and `kraken paper sell` only. Operator surfaces emit dry run CLI strings.
2. No real funds touched. The contest entry is the agent stack and the dashboard, not a live bot.
3. All keys in environment variables. The repo never carries secrets.

## License

MIT. See `LICENSE`. The mirrored Kraken CLI SKILL files retain their own MIT notice at `LICENSE.kraken-cli`.

## Credits

Built collaboratively with Anthropic's Claude. The Dog of Bitcoin Foundation is the maintainer.
