# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog, and the project uses Semantic Versioning.

## [0.1.0] 2026-05-23

Initial public scaffold.

### Added
- Backend skeleton (FastAPI on port 8000) with a `/health/providers` endpoint.
- Provider layer with a base class, a registry, and two implementations: DotSwap and the Kraken CLI wrapper.
- Indicator layer with a base class, a registry, and four implementations: `spread`, `vwap`, `signal_quality`, `onchain_heat`.
- Frontend skeleton (React, Vite) with one panel per indicator.
- Test scaffold for providers and indicators.
- Documentation: PROVIDERS, INDICATORS, RUNNING, CONTRIBUTING, PUBLISH.
- Deploy templates: systemd unit for the backend, nginx config for the static bundle.

### Planned (v0.2 candidates)
- Durable history for windowed indicators across process restarts.
- Optional secondary on-chain provider with a fallback policy.
- Agents layer fully fleshed out (Alpha and General named behaviors).

[0.1.0]: https://github.com/dog-of-bitcoin/dog-of-bitcoin/releases/tag/v0.1.0
