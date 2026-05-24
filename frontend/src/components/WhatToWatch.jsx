import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

function indexByName(list) {
  const out = {};
  for (const item of list || []) out[item.name] = item.envelope?.value;
  return out;
}

function pickCallout(indicators) {
  if (!indicators) return null;
  const spread = indicators.spread;
  const sq = indicators.signal_quality;
  const heat = indicators.onchain_heat;
  const vwap = indicators.vwap;

  if (heat?.score >= 75 && sq?.score >= 80 && spread?.spread_bps < 30) {
    return {
      tag: "BITE READY",
      color: "#f7931a",
      message: `heat ${heat.score.toFixed(0)}, quality ${sq.score.toFixed(0)}, tight spread. all 3 bite conditions met. bite strategy would fire on this cycle.`,
    };
  }
  if (heat?.score >= 65) {
    return {
      tag: "HEAT RISING",
      color: "#ffb35e",
      message: `onchain heat at ${heat.score.toFixed(0)}. fill rate, tvl, and velocity are running hot. chase strategy buys here.`,
    };
  }
  if (heat?.score <= 35 && heat?.score > 0) {
    return {
      tag: "HEAT FADING",
      color: "#c084fc",
      message: `onchain heat at ${heat.score.toFixed(0)}. activity is cooling. chase strategy sells here, dca holds position.`,
    };
  }
  if (sq?.score !== undefined && sq?.score < 50) {
    return {
      tag: "LOW SIGNAL",
      color: "#e85a8a",
      message: `signal quality at ${sq.score.toFixed(0)} (depth, freshness, agreement weak). agents will hold or shrink size until the book firms up.`,
    };
  }
  if (spread?.spread_bps !== undefined && spread.spread_bps > 60) {
    return {
      tag: "WIDE BOOK",
      color: "#c084fc",
      message: `spread at ${spread.spread_bps.toFixed(0)} bps. round trip is expensive. dca and bite will wait; chase only fires if heat is loud.`,
    };
  }
  if (sq?.score !== undefined && sq?.score >= 80 && heat?.score >= 40 && heat?.score <= 65) {
    return {
      tag: "STABLE BUILD",
      color: "#f7931a",
      message: `quality ${sq.score.toFixed(0)}, heat balanced. dca conditions ideal. patient accumulation window.`,
    };
  }
  if (vwap?.vwap && spread?.mid && Math.abs(spread.mid / vwap.vwap - 1) > 0.005) {
    const pct = ((spread.mid / vwap.vwap - 1) * 100).toFixed(2);
    return {
      tag: "VWAP DRIFT",
      color: "#ffb35e",
      message: `mid is ${pct}% off the 5 min vwap. price is leading or lagging recent flow. watch for snapback.`,
    };
  }
  return {
    tag: "QUIET",
    color: "#7a7088",
    message: "market is sleepy. indicators in their middle bands. agents wait for a setup.",
  };
}

export default function WhatToWatch() {
  const fetcher = useCallback(() => api.indicators(), []);
  const { data } = usePolling(fetcher, 5000);
  const callout = pickCallout(indexByName(data?.indicators));

  if (!callout) {
    return (
      <div className="watch-callout">
        <span className="watch-tag" style={{ color: "#7a7088" }}>WHAT TO WATCH</span>
        <span className="watch-msg muted">gathering signal...</span>
      </div>
    );
  }

  return (
    <div className="watch-callout" style={{ borderLeftColor: callout.color }}>
      <span className="watch-tag" style={{ color: callout.color }}>{callout.tag}</span>
      <span className="watch-msg">{callout.message}</span>
    </div>
  );
}
