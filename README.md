# DOG Ai

The agent stack for DOG on Bitcoin L1, built for Kraken's Agent Zero contest. 4 autonomous AI characters watch the DOG Rune across both the native Bitcoin L1 pool (DogSwap via Nexus) and Kraken, surfacing arbitrage opportunities that reward users on both venues.

> **v0.1.0 Release The Kraken**
> Kraken Agent Zero submission, deadline 2026-05-27.
> Live dashboard at [dogofbitcoin.io](https://dogofbitcoin.io)

## Why this exists

The DOG Rune lives natively on Bitcoin L1 and trades on Kraken. That means two venues, two liquidity pools, and a persistent spread between them. Most traders only see one side. This dashboard shows both, in real time, so users on either venue can spot when the gap is worth acting on.

The goal is not to pick sides. Kraken brings speed, depth, and global reach. Bitcoin L1 brings sovereignty, transparency, and the rune's native home. When both venues thrive, DOG holders win. The arbitrage signal is the bridge: it tells a Kraken trader when L1 is cheaper, and it tells an L1 holder when Kraken is offering a premium. No edge lasts forever, so the dashboard gives you a clean view of both sides to move swiftly.

## Foundation treasury

The dashboard opens with a cross venue treasury panel: on chain wallet balance (BTC + DOG from the foundation's Bitcoin L1 wallet via mempool.space) alongside the Kraken paper trading portfolio (DOG position, USD cash, PnL, trade count). Totals are unified across both venues so an arbitrage trader sees the full picture in one glance. When the arb spread widens, you know exactly what you are working with on each side.

The current treasury view is a demo using the Dog of Bitcoin Foundation wallet. In production, any DOG holder can connect their own wallet and see their personal on chain balance alongside their Kraken account. The architecture supports the Xverse REST API (`api.secretkeylabs.io`) for precise per address BTC and DOG rune balances, so users get real time wallet state without trusting a third party with their keys.

## The 4 agents

```
Dog of Bitcoin     main character    strategy picker + paper trader via Kraken CLI
Kraken             exchange ops      CLI surface, account state, dry run previews
Alpha              data confidence   signal quality scoring across both venues
General Ghost      directional       bullish, neutral, bearish regime narrator
```

Dog of Bitcoin is the decision maker. He reads the other 3 agents, picks one of 5 trading strategies based on the current market regime, and executes via the Kraken CLI paper trading engine. The supporting agents narrate the regime so the operator (or the dashboard viewer) understands why Dog of Bitcoin chose the strategy he did.

## Kraken CLI integration

The Kraken CLI is the backbone of every trading decision. This is not a REST API wrapper; every market interaction flows through the CLI binary as the skill packages recommend.

| CLI Command | Where Used | Purpose |
|---|---|---|
| `kraken ticker DOGUSD` | KrakenProvider | Real time DOGUSD pricing |
| `kraken ticker XBTUSD` | KrakenProvider | BTC leg for synthetic DOG/BTC construction |
| `kraken balance` | KrakenProvider, KrakenAgent | Account balance state before every decision |
| `kraken open-orders` | KrakenProvider, KrakenAgent | Verify no orphaned orders before new fills |
| `kraken trades-history` | KrakenProvider, KrakenAgent | Recent fills for performance tracking |
| `kraken spreads DOGUSD` | KrakenProvider, KrakenAgent | Historical spread data for regime detection |
| `kraken volume` | KrakenProvider | Fee tier and volume tracking |
| `kraken orderbook DOGUSD` | KrakenProvider | L2 book depth for slippage estimation |
| `kraken trades DOGUSD` | KrakenProvider | Recent public trades for momentum signals |
| `kraken order buy/sell --validate` | KrakenAgent, TraderAgent | Dry run order validation (no submission) |
| `kraken paper init` | TraderAgent | Initialize paper trading account |
| `kraken paper buy/sell` | TraderAgent | Execute paper trades |
| `kraken paper status` | TraderAgent | Portfolio state after each cycle |
| `kraken paper balance` | TraderAgent | Position sizing checks |
| `kraken status` | KrakenProvider | System health and liveness |
| `kraken order cancel-after` | Safety reference | Dead man's switch for autonomous sessions |

All 8 mirrored SKILL.md files from `krakenfx/kraken-cli` are loaded into the Trader's system prompt so the AI reads Kraken's own playbook before making decisions.

## Strategy rotation

The Trader auto rotates between 5 strategies based on live indicators:

| Strategy | Trigger | Kraken CLI Emphasis |
|---|---|---|
| DOG DCA | Default, calm market | `kraken paper buy` limit orders at the bid |
| Chase | Heat > 50, SQ > 50 | `kraken paper buy/sell` market orders for speed |
| Bite | Heat > 60, SQ > 80, spread < 30 bps | `kraken paper buy` tight limit inside the bid |
| Watchdog | Stale data or SQ < 30 | `kraken order --validate` dry runs only |
| Sats Stacker | Position profitable > 1.5% | `kraken paper sell` limit orders to accumulate BTC |

## Cross venue arbitrage

The arb spread indicator compares the DogSwap L1 pool price (via Nexus) against the Kraken synthetic DOG/BTC mid price (constructed from `kraken ticker DOGUSD` / `kraken ticker XBTUSD`). When the gap exceeds 2%, the dashboard flags it as actionable, showing users on both venues where the opportunity sits.

This is the bridge between L1 and Kraken. A Kraken user sees "DogSwap is 3% cheaper" and knows the L1 pool has value. An L1 user sees "Kraken is offering a 2.5% premium" and knows there is demand on the exchange. No edge lasts forever: the dashboard gives you the numbers, the treasury shows you what you have to work with, and the agents narrate the regime so you can move before the gap closes.

## Stack

| Layer | Tech | Notes |
|---|---|---|
| Backend | FastAPI, Python 3.11, uvicorn | Self registering providers, indicators, agents |
| Frontend | React, Vite | Real time dashboard with agent pose art |
| Exchange | Kraken CLI 0.3.2 | 16 CLI commands used across providers and agents |
| On chain | Nexus protocol | Reads the DogSwap DOG/BTC pool natively on Bitcoin L1 |
| AI | Claude (Anthropic) | Strategy decisions with prompt caching, skill file context |

## Autonomy progression

Following the `kraken-autonomy-levels` skill package:

- **v0.1 (current):** Level 2, paper trading. All decisions route through `kraken paper buy/sell`. No real funds at risk. The dashboard surfaces what the agent would do, with `--validate` dry runs for transparency.
- **v0.2 (planned):** Level 3, supervised trading. Real `kraken order` commands with human confirmation. Dead man's switch (`kraken order cancel-after 600`) active every session.
- **v0.3 (planned):** Level 4, autonomous within caps. Position limits, pair allowlists, and a read only monitoring agent running alongside.

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

Open `http://localhost:5173`. See `docs/RUNNING.md` for the full setup.

## Documentation

| Document | Covers |
|---|---|
| `CLAUDE.md` | Style rules, conventions for any Claude session on this repo |
| `docs/SUBMISSION.md` | Contest submission summary for judges |
| `docs/UI_SPEC.md` | Visual contract, layout, color tokens, components |
| `docs/COLLABORATION.md` | Two Claude workflow, file ownership, branch rules |
| `docs/PROVIDERS.md` | Provider interface contract |
| `docs/INDICATORS.md` | Indicator interface contract |
| `docs/CONTRIBUTING.md` | Tests, contribution rules |
| `docs/RUNNING.md` | Full local setup walkthrough |
| `docs/kraken-skills/` | 8 SKILL.md files mirrored from `krakenfx/kraken-cli` (MIT) |

## Hard constraints in v0.1

1. No live trading. Dog of Bitcoin uses `kraken paper buy` and `kraken paper sell` only.
2. No real funds touched. The contest entry is the agent stack and the dashboard.
3. All keys in environment variables. The repo never carries secrets.
4. Every order is validated via `kraken order --validate` before the paper engine fires.

## License

MIT. See `LICENSE`. The mirrored Kraken CLI SKILL files retain their own MIT notice at `LICENSE.kraken-cli`.

## Credits

Built collaboratively with Anthropic's Claude. The Dog of Bitcoin Foundation is the maintainer. Powered by the Kraken CLI and the Kraken exchange.
