"""Trader strategy definitions.

Each strategy is a small bundle:

  - name           short slug, used in the API and dashboard
  - title          human label
  - description    one or two lines for the UI
  - kraken_emphasis  which Kraken CLI surface(s) this strategy leans on
  - caps           per cycle and cooldown overrides
  - prompt_extra   instructions appended to the Trader's system prompt
  - order_type     "limit" | "market" | "none" (Watchdog never fires)

The Trader looks up the active strategy each cycle and composes the system
prompt + applies the caps. Changing strategy at runtime via the API takes
effect on the next cycle.

These strategies are informed by observing DOG across both Kraken and
Bitcoin L1 (DogSwap pool via Nexus):
  - Kraken brings deep liquidity, global reach, and tight spreads on
    DOGUSD. L1 brings the rune's native home and on chain transparency.
    The arb between the two venues is persistent and the signal that ties
    them together.
  - 88% of DogSwap pool swaps are partials, so L1 liquidity is fragmented.
    Each fire should be small enough to avoid the slippage cliff.
  - Kraken taker fee is 0.40%; maker fee is 0.23%. The DCA path leans
    maker, the Chase path eats taker for timing, Bite leans maker with
    tight limits, Watchdog never pays.
  - Cross venue spreads on DOG/BTC are usually under 50 bps but spike on
    news. Bite waits for the under-30 bps window.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Strategy:
    name: str
    title: str
    description: str
    kraken_emphasis: str
    max_trade_dog: float
    cooldown_s: int
    order_type: str  # "limit" | "market" | "none"
    prompt_extra: str


DOG_DCA = Strategy(
    name="dog-dca",
    title="DOG DCA",
    description=(
        "Patient accumulation. Steady small buys when signal_quality is healthy. "
        "Sells only on material profit or clear regime shift. Dog army energy."
    ),
    kraken_emphasis="kraken paper buy DOGUSD <vol> --type limit --price <bid> (maker intent)",
    max_trade_dog=2000.0,
    cooldown_s=60,
    order_type="limit",
    prompt_extra=(
        "Strategy: DOG DCA. Accumulate patiently on $DOG. Lean toward small buys "
        "every few cycles when signal_quality > 50 and heat is stable or rising. "
        "Sell when unrealised_pnl_pct > 1 percent and heat is trending down, "
        "or when heat collapses below 35. "
        "Avoid reactive flips. A steady cadence beats one big call. Use limit "
        "orders priced at the current bid; the runtime appends the limit price."
    ),
)


CHASE = Strategy(
    name="chase",
    title="Chase",
    description=(
        "Momentum. Buys when on chain heat is above 50 with signal quality above 50, "
        "sells when heat drops past 35. Takes the taker fee for speed."
    ),
    kraken_emphasis="kraken paper buy/sell DOGUSD <vol> --type market (instant fill)",
    max_trade_dog=5000.0,
    cooldown_s=30,
    order_type="market",
    prompt_extra=(
        "Strategy: Chase. Trend follow $DOG using on chain heat as your primary "
        "signal. Buy when heat is above 50 with healthy signal_quality above 50. "
        "Sell when heat crosses down through 35. Use market orders; speed beats "
        "fee here. Do not chase heat that has already cooled. If heat is below "
        "35, hold."
    ),
)


BITE = Strategy(
    name="bite",
    title="Bite",
    description=(
        "Sniper. Only fires when ALL conditions align: heat > 60, signal_quality > 80, "
        "spread < 30 bps. Quality over quantity. Long cooldown."
    ),
    kraken_emphasis="kraken paper buy DOGUSD <vol> --type limit --price <inside-the-bid>",
    max_trade_dog=1000.0,
    cooldown_s=300,
    order_type="limit",
    prompt_extra=(
        "Strategy: Bite. You are a sniper. Fire ONLY when ALL three conditions "
        "hold simultaneously: onchain_heat > 60, signal_quality > 80, "
        "spread_bps < 30. Otherwise hold; the cooldown is 5 minutes so wasted "
        "shots are expensive. When you fire, use a limit order priced one tick "
        "inside the current bid. Sell only on heat collapse below 40."
    ),
)


WATCHDOG = Strategy(
    name="watchdog",
    title="Watchdog",
    description=(
        "Observation only. Never places paper orders. Narrates regime, surfaces "
        "what an entry would look like via kraken order --validate dry runs."
    ),
    kraken_emphasis="kraken order ... --validate (dry run only)",
    max_trade_dog=0.0,
    cooldown_s=999_999,
    order_type="none",
    prompt_extra=(
        "Strategy: Watchdog. You do not place orders, ever. action must always be "
        "hold. Use the reasoning field to narrate the current regime in one tight "
        "sentence: which way the indicators lean, whether a Chase or Bite would "
        "fire here, and what size and price an entry would target. Operator reads "
        "this to learn the rune's behaviour without risking the position."
    ),
)


SATS_STACKER = Strategy(
    name="sats-stacker",
    title="Sats Stacker",
    description=(
        "BTC accumulation. When the DOG position is profitable, sells small "
        "chunks to stack sats. Holds or buys dips when underwater. Turns "
        "DOG momentum into realized BTC gains."
    ),
    kraken_emphasis="kraken paper sell DOGUSD <vol> --type limit --price <ask> (take profit into BTC)",
    max_trade_dog=2000.0,
    cooldown_s=90,
    order_type="limit",
    prompt_extra=(
        "Strategy: Sats Stacker. Your goal is to accumulate BTC from DOG profits. "
        "When unrealised_pnl_pct > 1 percent, sell small chunks (500 to 2000 DOG) "
        "at the ask to realize gains into BTC. Sell more aggressively when pnl > 2 "
        "percent. When unrealised_pnl_pct is negative or below 0.5 percent, hold or "
        "buy small dips if signal_quality > 70 and heat > 50. Never sell below cost "
        "basis unless heat collapses below 30 (cut losses). Use limit orders at the "
        "current ask. The point is patient profit taking, not panic selling."
    ),
)


REGISTRY: dict[str, Strategy] = {
    s.name: s for s in (DOG_DCA, CHASE, BITE, WATCHDOG, SATS_STACKER)
}

DEFAULT_STRATEGY = DOG_DCA.name


def get_strategy(name: str) -> Strategy:
    return REGISTRY.get(name, REGISTRY[DEFAULT_STRATEGY])


def list_strategies() -> list[dict]:
    return [
        {
            "name": s.name,
            "title": s.title,
            "description": s.description,
            "kraken_emphasis": s.kraken_emphasis,
            "max_trade_dog": s.max_trade_dog,
            "cooldown_s": s.cooldown_s,
            "order_type": s.order_type,
        }
        for s in REGISTRY.values()
    ]
