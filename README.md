# Dog of Bitcoin

A live dashboard for the $DOG Rune on Bitcoin. It combines on-chain data from DotSwap with market data from Kraken, and surfaces the result through a small set of self-contained indicators and agents.

Version: 0.1.0 (read only on the trading side).

## Quick start

See `docs/RUNNING.md` for the full setup. The short version:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # fill in DOTSWAP_API_KEY
uvicorn app:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## What is inside

| Layer | Lives in | One liner |
|---|---|---|
| Providers | `backend/providers/` | Pull data from DotSwap and the Kraken CLI |
| Indicators | `backend/indicators/` | Turn raw data into named signals |
| Agents | `backend/agents/` | Read indicators, produce a stance |
| Dashboard | `frontend/` | Render panels for each indicator and agent |

Each layer is decoupled. Adding a new provider, indicator, or agent does not require touching the others. See `docs/PROVIDERS.md` and `docs/INDICATORS.md` for the contracts.

## What v0.1 is and is not

**Is:** a read only dashboard. It fetches, computes, and renders. Operator actions are surfaced as dry run Kraken CLI strings the user can run themselves.

**Is not:** an automated trader. No orders are placed by the dashboard. See `docs/CONTRIBUTING.md` for why this stays read only in v0.1.

## License

MIT. See `LICENSE`.
