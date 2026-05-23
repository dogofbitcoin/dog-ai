# Providers

One line summary of each provider in v0.1.

| Name | Kind | What it returns |
|---|---|---|
| `dotswap` | onchain | $DOG Rune snapshot: floor, 24h volume, holder count, recent fills, top of book depth. 60 second in memory cache. |
| `kraken` | market | DOGBTC ticker, recent trades, top of book orderbook via the Kraken CLI. DOGBTC is synthesised from DOGUSD and XBTUSD because Kraken does not list a direct DOG/BTC market. |

Add a new provider by creating `backend/providers/<name>.py`, subclassing `Provider`, and calling `register()` at the bottom of the file. Add a row to this table.
