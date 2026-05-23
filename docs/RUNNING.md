# Running

How to run Dog of Bitcoin v0.1 locally for development and on the AWS box for the live dashboard.

## What you need

- Python 3.11 or later
- Node 20 or later
- The Kraken CLI installed and on `PATH` (only required on the machine that fetches market data)
- A DotSwap API key
- 1 GB RAM minimum, 2 GB recommended

## First-time setup

Clone the repo, then from the project root:

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

Copy the env template at the repo root and fill in the values:

```bash
cp .env.example .env
```

Minimum required values for v0.1:

```
DOTSWAP_API_BASE=https://api.dotswap.app
DOTSWAP_API_KEY=<your key>
KRAKEN_CLI_PATH=kraken
KRAKEN_PAIR=DOGBTC
```

Optional values are listed and commented in `.env.example`.

## Running locally for development

Two processes, two terminals.

**Backend** (from `backend/`):
```bash
source .venv/bin/activate
uvicorn app:app --reload --port 8000
```

**Frontend** (from `frontend/`):
```bash
npm run dev
```

The frontend dev server runs on port 5173 and proxies API calls to `localhost:8000`. Open `http://localhost:5173` and the dashboard renders with live data.

## Health check

Before anything else, confirm the providers are reachable:

```bash
curl http://localhost:8000/health/providers
```

You should see entries for `dotswap` and `kraken` with `ok: true`. If either is false, the `note` field tells you what failed. Common ones:

- `dotswap: ok=false, note="missing DOTSWAP_API_KEY"` — set the env var, restart.
- `kraken: ok=false, note="kraken CLI not on PATH"` — install the CLI or set `KRAKEN_CLI_PATH`.

## Running on the AWS box

The AWS instance is a 2 CPU / 8 GB box. v0.1 fits comfortably. The pattern:

1. Clone the repo to `~/dog-of-bitcoin`.
2. Run the same first-time setup as above.
3. Use `systemd` units (not bare processes) so the services restart on reboot and on crash.

Example unit for the backend (`/etc/systemd/system/dob-backend.service`):

```ini
[Unit]
Description=Dog of Bitcoin backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/dog-of-bitcoin/backend
EnvironmentFile=/home/ubuntu/dog-of-bitcoin/.env
ExecStart=/home/ubuntu/dog-of-bitcoin/backend/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Build the frontend once and let the backend (or nginx) serve the static bundle:

```bash
cd frontend
npm run build
# outputs to frontend/dist/
```

Then either point nginx at `frontend/dist/` or let the backend serve it from `/static`. The repo includes both options in `deploy/`.

Enable and start:

```bash
sudo systemctl enable --now dob-backend
```

Check it:

```bash
sudo systemctl status dob-backend
curl http://localhost:8000/health/providers
```

## Running the test suite

**Backend** (from `backend/`):
```bash
source .venv/bin/activate
pytest
```

**Frontend** (from `frontend/`):
```bash
npm test
```

Tests are deterministic — no network, no clock, no randomness. If a test starts flaking it's a bug, not a flake.

## Running with the AWS Claude agent

The AWS box has Claude Code installed. To let it work on the repo:

```bash
cd ~/dog-of-bitcoin
claude
```

Claude Code reads `CLAUDE.md` from the repo root on session start. That file holds the project conventions and the branch rules. Sessions started with `claude -r` resume the prior session and do NOT re-read `CLAUDE.md` — if you change the file, start a fresh session with `claude` to pick up the changes.

The AWS agent commits to the `claude-aws` branch only. To push:

```bash
git checkout claude-aws
git add -A
git commit -m "<message>"
git push origin claude-aws
```

The bot identity should already be configured via:

```bash
git config user.name "dog-of-bitcoin-bot"
git config user.email "bot@dogofbitcoin.com"
```

Set those once in the repo and every commit from the AWS box carries them.

## Logs

- Backend logs go to stdout. Under systemd: `journalctl -u dob-backend -f`.
- Frontend dev logs go to the terminal running `npm run dev`.
- No log files are written to disk in v0.1. Add a file handler in `backend/log.py` if you need persistence.

## Stopping everything

Local:
```
Ctrl+C in each terminal
```

AWS:
```bash
sudo systemctl stop dob-backend
```

## When something is wrong

In order:

1. `curl http://localhost:8000/health/providers` — is the data layer alive?
2. `journalctl -u dob-backend -n 100` — what did the backend log?
3. Browser console — what does the frontend say?
4. `pytest backend/providers/tests/` — do the provider tests still pass against the live endpoints?

If all four are clean and the dashboard still looks wrong, the bug is in an indicator or agent. Pull the relevant module's test and run it in isolation.
