# UI_SPEC

Visual + interaction contract for the Dog of Bitcoin dashboard.

This document is the single source of truth for layout, color, typography, motion, and component behavior. Implementation must match it. When the live UI drifts from this spec, update the spec from the latest screenshot, then bring the implementation back into line.

**Who writes this:** the Claude session that has direct visual access (currently desktop Claude with screenshots from `docs/reference/`). Sections marked `(TBD)` are placeholders waiting on that session.

**Who implements:** any session (AWS Claude included). Implementers do not need to view screenshots; they read this spec and the referenced design tokens.

**Voice + copy rules:** see root `CLAUDE.md`. No dashes in prose, numerical figures, no emoji in code or docs.

---

## 1. Layout grid

Locked decisions:

- Container: `max-width: 1480px`, side padding `12px`
- Density: Bloomberg-terminal feel (compact, multi-column, horizontal)
- Typography: `ui-monospace` stack everywhere
- Color palette: orange (DOG, #f7931a), purple (Kraken, #8b5cf6 + #c084fc), white (#f8f8ff)

Region layout (top to bottom):

| Region | Height | Contents |
|---|---|---|
| Header | 56 px | Brand, version chip, health pills (right) |
| Character strip | TBD | 4 avatar tiles in a row, stance pill on each, pulse dot when active |
| Indicator strip | TBD | 4 compact metric cards in one row (spread, vwap, signal quality, onchain heat), each with sparkline + bar |
| Main agents row | TBD | Trader (left, 60%) and Kraken (right, 40%), both tabbed |
| Support row | TBD | Alpha and General Ghost as compact half-width cards |
| Footer | 32 px | Disclosure copy |

Detailed grid sizes, gap values, breakpoints: (TBD by desktop Claude from screenshot).

## 2. Color tokens

Canonical values live in `frontend/src/index.css` under `:root`. This spec references them by name; do not redefine literals here.

| Token | Use |
|---|---|
| `--orange` (#f7931a) | DOG brand, buy intent, confident, bullish, ok pill, primary bars |
| `--orange-soft` (#ffb35e) | Strategy_change action, tentative, neutral |
| `--orange-deep` (#c46a00) | Bar gradient anchor |
| `--purple` (#8b5cf6) | Kraken brand, sell intent, exchange context |
| `--purple-light` (#c084fc) | Section labels, panel titles, sell action, bearish |
| `--purple-deep` (#6d28d9) | Bar gradient anchor |
| `--white` (#f8f8ff) | Primary text, big numbers |
| `--text-soft` (#c4bcd4) | Body copy |
| `--text-mute` (#7a7088) | Keys, secondary copy, hold action |
| `--bg` (#0d0814) | App background |
| `--bg-card` (#171122) | Panel background |
| `--bg-block` (#1d1530) | Inner blocks |
| `--border` (#2a1f3a) | Panel borders |
| `--bad` (#e85a8a) | Halted, drawdown, error pills |

Disallowed (legacy): green `#62b67a`, gold `#e2bb53`, red `#d36a6a`, neutral gray `#9a9a9a`. If you find them, replace with the equivalent above.

## 3. Component inventory

Live components in `frontend/src/components/`. Each entry below lists name, file, current data source, and what the spec mandates beyond what code already does.

| Component | File | Source | Spec adds |
|---|---|---|---|
| HealthBar | `HealthBar.jsx` | `/api/health/providers` | (TBD: position, density) |
| TraderPanel | `TraderPanel.jsx` | `/api/agents/trader` | (TBD: tabs, sparklines, risk meter) |
| KrakenPanel | `KrakenPanel.jsx` | `/api/agents/kraken` | (TBD: tabs, ticker layout) |
| AlphaPanel | `AlphaPanel.jsx` | `/api/agents/alpha` | (TBD: compact mode) |
| GeneralPanel | `GeneralPanel.jsx` | `/api/agents/general` | (TBD: compact mode) |
| SpreadPanel | `SpreadPanel.jsx` | `/api/indicators/spread` | (TBD: sparkline) |
| VwapPanel | `VwapPanel.jsx` | `/api/indicators/vwap` | (TBD: sparkline) |
| SignalQualityPanel | `SignalQualityPanel.jsx` | `/api/indicators/signal_quality` | (TBD: chip variant) |
| OnchainHeatPanel | `OnchainHeatPanel.jsx` | `/api/indicators/onchain_heat` | (TBD: chip variant) |

New components defined by this spec (to be implemented):

- `CharacterStrip` (TBD) — horizontal row of 4 avatars with stance state
- `CharacterAvatar` (TBD) — Lottie/Rive container per character, props: name, stance, size
- `IndicatorChip` (TBD) — compact indicator card variant for the strip
- `RiskMeter` (TBD) — gauge inside TraderPanel
- `Sparkline` (TBD) — small SVG trend line

## 4. Voice + copy rules

Inherited from `CLAUDE.md`:

1. No dashes in prose. Use commas, semicolons, or rewrite.
2. Numerical figures, not words. "5 providers", "20%".
3. No emoji in code, commits, or docs.
4. Lowercase agent names in UI ("agent dog of bitcoin", "agent kraken").

UI-specific (TBD by desktop Claude):

- Tone for tooltips, helper text, error states
- Plain-language tooltips for entry to mid level traders
- Glossary entries and where they surface

## 5. Scene tag format

Screenshots in `docs/reference/` follow this naming convention so the spec can point at a specific visual:

```
dashboard-<version>-<scene>-<state>.png
```

Examples:
- `dashboard-v1-baseline-trading.png`
- `dashboard-v1-trader-tab-portfolio.png`
- `dashboard-v1-character-strip-idle.png`
- `dashboard-v1-empty-state.png`

When this spec references a screenshot, it uses the bare filename: see `dashboard-v1-baseline-trading.png`.

## 6. Characters + animation

Locked decision: Lottie or Rive based animations, one file per character, served from `frontend/src/assets/characters/`.

| Character | Avatar file | States |
|---|---|---|
| Dog of Bitcoin | `dog-of-bitcoin.json` | idle, trading, halted (TBD) |
| Alpha | `alpha.json` | confident, tentative, blind (TBD) |
| General Ghost | `general-ghost.json` | bullish, neutral, bearish (TBD) |
| Kraken | `kraken.json` | tight-book, wide-book, low-signal, watching (TBD) |

(TBD: pose specification per state, motion durations, loop behavior, hover behavior.)

## 7. Helpers for entry to mid level traders

(TBD by desktop Claude. Candidates discussed: plain-language tooltips, "what to watch right now" callout, risk meter, sparklines behind numbers, glossary chip row.)

## 8. Change log

| Date | Version | Author | Change |
|---|---|---|---|
| 2026-05-24 | v1-scaffold | aws claude | initial scaffold, sections 1, 2, 3, 4, 5 partly filled, sections 6 and 7 TBD |
