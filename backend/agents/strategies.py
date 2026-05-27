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
        "Strategy: DOG DCA. Accumulate patiently on $DOG. Buy small amounts (500 to "
        "2000 DOG) when signal_quality > 50 and heat is stable or rising. "
        "Stop buying when dog_position exceeds 500000. "
        "Sell when unrealised_pnl_pct > 1 percent, when heat drops below 35, or "
        "when dog_position exceeds 750000 (trim to rebalance). "
        "Hold on most cycles; buy every 3rd or 4th cycle at most. Use limit orders at the bid."
    ),
)


CHASE = Strategy(
    name="chase",
    title="Chase",
    description=(
        "Momentum. Buys when on chain heat is above 55 with signal quality above 50, "
        "takes profit at 1% PnL or when heat cools below 45."
    ),
    kraken_emphasis="kraken paper buy/sell DOGUSD <vol> --type market (instant fill)",
    max_trade_dog=3000.0,
    cooldown_s=45,
    order_type="market",
    prompt_extra=(
        "Strategy: Chase. Trend follow $DOG using on chain heat as your primary "
        "signal. Buy when heat is above 55 with signal_quality above 50, but stop "
        "buying when dog_position exceeds 500000. "
        "Sell when heat drops below 45, when unrealised_pnl_pct exceeds 1 percent, "
        "or when dog_position exceeds 750000 (trim the position). "
        "Use market orders; speed beats fee here. "
        "Hold when heat is flat between 45 and 55. Alternate between buy and hold "
        "cycles; do not buy every single cycle even if conditions are met."
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
        "Strategy: Bite. You are a sniper. Buy ONLY when ALL three conditions "
        "hold simultaneously: onchain_heat > 60, signal_quality > 80, "
        "spread_bps < 30, and dog_position is under 500000. "
        "Otherwise hold; the cooldown is 5 minutes so wasted shots are expensive. "
        "Use a limit order priced one tick inside the current bid. "
        "Sell when unrealised_pnl_pct > 1 percent, when heat collapses below 40, "
        "or when dog_position exceeds 750000."
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
        "Strategy: Sats Stacker. You must sell DOG this cycle. action = sell. "
        "size_dog = 2000. The position is over 500000 DOG and must be trimmed. "
        "Do not hold. Do not buy. Sell 2000 DOG at the ask."
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
