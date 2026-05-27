import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

function fmtTime(ts) {
  if (!ts) return "";
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function fmtVol(v) {
  if (!v) return "0";
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
  return v.toFixed(0);
}

export default function TradeFeed() {
  const fetcher = useCallback(() => api.krakenTrades(), []);
  const { data } = usePolling(fetcher, 5000);
  const trades = data?.trades;

  return (
    <div className="panel panel-trades">
      <div className="name">
        <span>live trades</span>
        <span className="muted">DOGUSD · Kraken</span>
      </div>
      {!trades || trades.length === 0 ? (
        <div className="value muted">loading</div>
      ) : (
        <div className="trade-list">
          {trades.slice(0, 20).map((t, i) => {
            const isBuy = t.side === "buy";
            return (
              <div key={i} className={`trade-row ${isBuy ? "trade-buy" : "trade-sell"}`}>
                <span className="trade-time">{fmtTime(t.ts)}</span>
                <span className={`trade-side ${isBuy ? "buy" : "sell"}`}>
                  {isBuy ? "BUY" : "SELL"}
                </span>
                <span className="trade-price">{t.price?.toFixed(6)}</span>
                <span className="trade-vol">{fmtVol(t.volume)}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
