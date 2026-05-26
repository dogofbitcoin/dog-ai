import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";
import { useSparkline } from "../hooks/useSparkline.js";
import Sparkline from "./Sparkline.jsx";

function fmtSats(btc) {
  if (!btc) return "—";
  return (btc * 1e8).toFixed(3);
}

function fmtPct(n) {
  if (n === undefined || n === null) return "—";
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

const DIRECTION_LABEL = {
  dotswap_cheaper: "DogSwap is cheaper",
  kraken_cheaper: "Kraken is cheaper",
  parity: "prices aligned",
};

export default function ArbPanel() {
  const fetcher = useCallback(() => api.indicator("arb_spread"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const v = env?.value;
  const stale = env?.meta?.stale;
  const gapHistory = useSparkline(v?.gap_pct);

  const gapColor = !v ? "var(--text-mute)"
    : v.actionable ? "var(--orange)"
    : "var(--text-soft)";

  return (
    <div className={`panel panel-arb ${stale ? "stale" : ""} ${v?.actionable ? "arb-hot" : ""}`}>
      <div className="name">
        <span data-tip="price gap between DogSwap (bitcoin L1 pool) and Kraken (centralized exchange). when the gap is wide enough to cover fees, there is an arbitrage opportunity moving DOG between venues.">
          arb spread
        </span>
        <span className="muted">L1 vs CEX</span>
      </div>
      {!v ? (
        <div className="value muted">{env?.meta?.notes || "loading"}</div>
      ) : (
        <>
          <div className="value-row">
            <div className="value" style={{ color: gapColor }}>{fmtPct(v.gap_pct)}</div>
            <Sparkline data={gapHistory} color={gapColor} />
          </div>

          {v.actionable && (
            <div className="arb-callout">
              {v.action_hint}
            </div>
          )}

          <div className="row">
            <span className="k" data-tip="DOG price on DogSwap L1 pool, derived from the most recent swap.">dogswap</span>
            <span>{fmtSats(v.dotswap_price_btc)} sats</span>
          </div>
          <div className="row">
            <span className="k" data-tip="DOG price on Kraken, midpoint of synthetic DOGBTC bid and ask.">kraken</span>
            <span>{fmtSats(v.kraken_mid_btc)} sats</span>
          </div>
          <div className="row">
            <span className="k" data-tip="direction of the price gap and which venue is cheaper right now.">edge</span>
            <span style={{ color: v.actionable ? "var(--orange)" : "var(--text-mute)" }}>
              {DIRECTION_LABEL[v.direction] || v.direction}
            </span>
          </div>
          <div className="row">
            <span className="k" data-tip="minimum gap percentage before the arb is considered worth acting on, accounting for fees on both sides.">threshold</span>
            <span>{v.threshold_pct}%</span>
          </div>

          <div className="arb-venues">
            <div className="arb-venue">
              <div className="arb-venue-label">DogSwap L1</div>
              <div className="row"><span className="k">24h vol</span><span>{v.dotswap_volume_24h_btc.toFixed(4)} BTC</span></div>
              <div className="row"><span className="k">fills 24h</span><span>{v.dotswap_fill_count_24h}</span></div>
              <div className="row"><span className="k">TVL</span><span>{(v.dotswap_tvl_dog / 1e6).toFixed(2)}M DOG</span></div>
            </div>
            <div className="arb-venue">
              <div className="arb-venue-label">Kraken CEX</div>
              <div className="row"><span className="k">bid</span><span>{fmtSats(v.kraken_bid_btc)} sats</span></div>
              <div className="row"><span className="k">ask</span><span>{fmtSats(v.kraken_ask_btc)} sats</span></div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
