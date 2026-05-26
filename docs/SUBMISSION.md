# Agent Zero Submission: Dog of Bitcoin

## The pitch (30 seconds)

Dog of Bitcoin is a live dashboard where 4 AI agents watch the DOG Rune across Kraken and Bitcoin L1 simultaneously. It surfaces cross venue arbitrage opportunities in real time, with a unified treasury view of both on chain and Kraken holdings so traders can move swiftly. No edge lasts forever. Every trading decision flows through the Kraken CLI.

**Live demo:** [dogofbitcoin.io](https://dogofbitcoin.io)

## What the judges see on the dashboard

At the top: the **foundation treasury**, a cross venue balance sheet. On chain wallet (Bitcoin L1: DOG rune balance + BTC) next to the Kraken paper trading portfolio (DOG position, USD cash, PnL, trade count), with unified totals. An arb trader sees exactly what they have to work with on each side before the edge closes.

Below that, 4 agents in a grid, each with unique character art that reacts to their current state (36 poses across 4 characters).

- **Dog of Bitcoin** (top left): The main character. He picks 1 of 5 trading strategies every 30 seconds based on market regime, then executes paper trades via `kraken paper buy/sell`. His panel shows active strategy, position, PnL, and a decision log.

- **Kraken** (top right): The exchange specialist. Surfaces live DOGUSD pricing, dry run previews (`kraken order --validate`), account balance, open orders, recent fills, and which of the 8 SKILL.md packages is most relevant right now.

- **Alpha** (bottom left): The data confidence scorer. Tabs for signal quality breakdown (freshness, depth, cross venue agreement), regime interpretation, and sparkline history.

- **General Ghost** (bottom right): The directional narrator. Tabs for on chain heat scoring, spread tracking, and regime calls (bullish/neutral/bearish).

Below the grid: a cross venue arb panel comparing DogSwap L1 pool price vs Kraken synthetic DOG/BTC, with a sparkline of the spread over time. Glows orange when the gap exceeds 2% (actionable). No edge lasts forever, so the arb panel + treasury together give traders a complete picture: what the gap is, and what they can deploy.

## Innovation and originality

1. **Cross venue L1 to CEX bridge.** Most trading agents operate on a single venue. This one reads the native Bitcoin L1 pool (DogSwap via Nexus protocol) and Kraken side by side, then expresses the gap as an actionable arbitrage signal. The insight: Kraken's global liquidity and Bitcoin L1's native sovereignty are complementary, and the spread between them is the signal that proves it.

2. **4 character agent architecture.** Instead of one monolithic trading bot, the work is split across 4 specialized agents with distinct personalities and art. The Trader (Dog of Bitcoin) only decides after consulting the data scorer (Alpha), the regime caller (General Ghost), and the exchange specialist (Kraken). This mirrors how a real trading desk operates.

3. **Auto strategy rotation.** The system reads 4 live indicators (on chain heat, signal quality, spread, PnL) and rotates between 5 strategies in real time. This is not a fixed algorithm; it is a regime adaptive framework where the AI picks the playbook that matches the current market.

4. **Unified cross venue treasury.** The dashboard opens with a single panel showing both the on chain Bitcoin L1 wallet (BTC + DOG rune balance via mempool.space) and the Kraken paper trading portfolio (DOG, USD, PnL) side by side with unified totals. An arb trader sees what they can deploy on each venue before acting. No edge lasts forever, so speed of assessment matters. The current view uses the Dog of Bitcoin Foundation wallet as a demo; in production, any DOG holder connects their own wallet via the Xverse API for precise, real time BTC and rune balances.

5. **Dynamic pose art.** Each agent has 9 unique PNG poses. A client side pose picker reads the agent's state (stance, intent, reasoning keywords) and crossfades to the matching image. The characters react visually to what is happening in the market.

## Technical execution

- **Self registering architecture.** Providers, indicators, and agents register at import time. No central wiring file. Adding a new data source or agent is one Python file.
- **Synthetic pair construction.** Kraken does not list a direct DOG/BTC market. We synthesize it from `kraken ticker DOGUSD` / `kraken ticker XBTUSD`, constructing bid/ask/last/VWAP for the synthetic pair with proper cross rate math.
- **Prompt caching.** Every Anthropic API call uses explicit `cache_control: {"type": "ephemeral"}` on system prompts. The 8 SKILL.md files are cached across cycles, reducing input token costs by ~90%.
- **10 test files** covering providers, indicators, and agents. Deterministic, no network, no clock.
- **Systemd services** with auto restart, SSL via Let's Encrypt, nginx reverse proxy.

## Use of Kraken CLI functionality

16 distinct CLI commands are used across the codebase:

**Market data:** `kraken ticker`, `kraken trades`, `kraken orderbook`, `kraken spreads`
**Account state:** `kraken balance`, `kraken open-orders`, `kraken trades-history`, `kraken volume`
**Paper trading:** `kraken paper init`, `kraken paper buy`, `kraken paper sell`, `kraken paper status`, `kraken paper balance`
**Safety:** `kraken order --validate` (dry run), `kraken order cancel-after` (dead man's switch reference), `kraken status` (liveness)

All 8 SKILL.md files from `krakenfx/kraken-cli` are loaded into the Trader's system prompt:
- `kraken-autonomy-levels` (operating at Level 2, paper trading)
- `kraken-dca-strategy` (informs the DOG DCA and Sats Stacker strategies)
- `kraken-error-recovery` (error categorization in agent error handling)
- `kraken-paper-strategy` (paper trading best practices)
- `kraken-rate-limits` (rate limit awareness in cycle timing)
- `kraken-shared` (CLI conventions, JSON output parsing)
- `kraken-spot-execution` (order type selection, slippage awareness)
- `recipe-start-dca-bot` (DCA recipe adapted for DOG regime)

The Kraken agent dynamically picks which skill package is most relevant based on the current regime (tight spread -> DCA skill, high heat -> spot execution skill, low signal -> error recovery skill).

## Practical usefulness

**For Kraken users:** See when the Bitcoin L1 pool is offering DOG cheaper than Kraken. The arb panel quantifies the gap in real time, and the treasury shows your Kraken balance right next to the on chain state. When the spread widens, you know what you have to work with on both sides. No edge lasts forever.

**For Bitcoin L1 users:** See when Kraken is offering a premium for DOG. The same arb signal works in reverse. If Kraken bid is 3% above the L1 pool floor, the treasury panel shows your on chain DOG holdings and the arb panel shows how wide the gap is. Both sides of the trade, one screen.

**For DOG holders generally:** Understand the regime. Is on chain activity heating up? Is signal quality strong or degraded? Is the spread tight enough for a DCA entry? The 4 agents narrate this continuously, in language the community already uses. The treasury gives context: here is what the foundation holds, here is how the paper trader is performing, here is the combined picture.

**For developers:** The self registering architecture is a template. Swap DogSwap for any Bitcoin L1 protocol, swap DOGUSD for any Kraken pair, and the same agent framework adapts. The Kraken CLI skill integration pattern (load SKILL.md files into the system prompt, dynamically pick the relevant one) is reusable for any CLI agent project.

## What is next

- **Personal wallet integration.** Replace the demo foundation wallet with per user wallet connection via the Xverse REST API (`api.secretkeylabs.io`). Users see their own BTC and DOG rune balances in real time, alongside their Kraken account, in one unified treasury view. Read only, no keys shared.
- **Level 3 graduation.** Supervised live trading with `kraken order buy/sell` and human confirmation, gated by `--validate` first.
- **WebSocket migration.** Move from `kraken ticker` polling to `kraken ws ticker BTC/USD` streaming for zero REST rate limit cost.
- **Batch orders.** Use `kraken order batch` for ladder entries on high heat regimes.
- **Dead man's switch in production.** `kraken order cancel-after 600` refreshed every cycle, so orders auto cancel if the agent crashes.

## Repository

[github.com/dogofbitcoin/dog-ai](https://github.com/dogofbitcoin/dog-ai)

Branch: `claude-aws` (active development), `develop` (integration), `main` (releases).
