# Contributing

Thanks for looking. This project is v0.1 and intentionally small. The structure is designed so that providers, indicators, and agents can be added without touching what already works.

## Branch model

| Branch | Purpose | Who pushes |
|---|---|---|
| `main` | Curated, reviewed, releasable | Maintainers only, via PR |
| `develop` | Integration branch for the next release | Maintainers, via PR |
| `claude-aws` | Autonomous work from the AWS agent | The AWS bot identity, direct push allowed |
| `feature/<name>` | Human contributor work | Anyone, via PR into `develop` |

`main` is protected. All merges to `main` go through a pull request from `develop`. No direct pushes, no force-pushes, ever.

## Pull request flow

1. Branch from `develop`: `git checkout -b feature/<short-name> develop`
2. Make your change. Keep PRs focused — one provider, one indicator, one fix.
3. Run the test suite locally (see `docs/RUNNING.md`).
4. Open a PR into `develop`. Fill the PR template.
5. A maintainer reviews. Squash-merge on approval.
6. Releases cut from `develop` into `main` and tag a version.

## Commit style

Plain, present-tense, no scope prefix required. Aim for one logical change per commit.

```
add onchain_heat indicator
fix dotswap timeout handling
docs: clarify provider registration
```

Commits from the AWS bot identity (`dog-of-bitcoin-bot <bot@dogofbitcoin.com>`) follow the same style but are confined to the `claude-aws` branch. Maintainers cherry-pick or merge those into `develop` after review.

## Code style

### Python (`backend/`)
- Python 3.11+
- Format with `black`, line length 100
- Lint with `ruff` using the config in `pyproject.toml`
- Type hints on public functions and provider/indicator interfaces
- Docstrings on every public class and function — one line is fine if it's clear

### JavaScript/React (`frontend/`)
- Node 20+
- Format with `prettier`
- Lint with `eslint` using the config in `frontend/.eslintrc`
- Function components only, no class components
- Hooks live in `frontend/src/hooks/`, one file per hook

### Both
- No dashes in prose written into the codebase, docs, or commit messages. Use commas, semicolons, or rewrite. This applies to README, doc comments, PR descriptions, and any user-facing copy.
- Numerical figures, not words. "5 providers" not "five providers". "20%" not "twenty percent".
- No emoji in code, commits, or docs.

## Adding new code

| Type | Where it goes | Doc to update |
|---|---|---|
| Data source | `backend/providers/<name>.py` | `docs/PROVIDERS.md`, `backend/providers/README.md` |
| Computation | `backend/indicators/<name>.py` | `docs/INDICATORS.md`, `backend/indicators/README.md` |
| Agent behavior | `backend/agents/<name>.py` | inline docstring, plus `CHANGELOG.md` if behavior shifts |
| UI component | `frontend/src/components/<Name>.jsx` | none, keep components self-documenting |
| Env var | `.env.example` | the doc that owns the consumer |

Every new file should be small enough to read in one screen on its first commit. If a single provider or indicator grows past 200 lines, that's a hint it wants to split.

## Testing

- Backend tests live next to the module they test: `backend/providers/tests/`, `backend/indicators/tests/`.
- Frontend tests live next to the component: `frontend/src/components/__tests__/`.
- New providers and indicators must ship with at least one test that exercises the public interface.
- See `docs/RUNNING.md` for commands.

## Issues and proposals

- Bug reports: open an issue with reproduction steps, expected output, actual output.
- Feature proposals: open an issue first to discuss before PR. Keeps wasted work low.
- Security: do not open a public issue. Email the maintainer address in the org profile.

## License

MIT. By contributing, you agree your contributions are licensed under the same MIT license that covers the project. See `LICENSE`.

## What this project will and will not accept

**Will:** new providers, new indicators, new agent behaviors that match the existing voice rules, frontend polish, docs improvements, test coverage, performance fixes.

**Will not:** automated order placement, real-money trading hooks, scraping of competitor sites, anything that requires a private API key to be committed, anything that adds a dependency without justification.

The project deliberately stays read-only on the trading side in v0.1. Operator actions are emitted as dry-run CLI commands for the user to run, never executed by the dashboard. PRs that try to change that will be closed.

## Releases

Versioning is semver in `VERSION`. v0.1 is the public baseline. Patch bumps for fixes, minor bumps for new providers or indicators that do not break existing consumers, major bumps for interface changes to `Provider` or `Indicator`. Every release adds a section to `CHANGELOG.md`.
