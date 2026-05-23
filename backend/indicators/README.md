# Indicators

One line summary of each indicator in v0.1.

| Name | Inputs | Window | What it returns |
|---|---|---|---|
| `spread` | kraken | snapshot | Top of book bid, ask, mid, spread in basis points. |
| `vwap` | kraken | 300s | Rolling volume weighted average price over the configured window. |
| `signal_quality` | kraken, dotswap | snapshot | 0 to 100 composite of freshness, depth, and cross source agreement. |
| `onchain_heat` | dotswap | snapshot | 0 to 100 composite of fill rate, holder count, and volume velocity. |

Add a new indicator by creating `backend/indicators/<name>.py`, subclassing `Indicator`, and calling `register()` at the bottom of the file. Add a row to this table.
