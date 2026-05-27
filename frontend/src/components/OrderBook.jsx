import { useCallback, useMemo } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

function fmtVol(v) {
  if (!v) return "0";
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return v.toFixed(0);
}

function DepthBar({ pct, side }) {
  return (
    <div className="depth-bar-bg">
      <div
        className={`depth-bar-fill ${side}`}
        style={{ width: `${Math.min(100, pct)}%` }}
      />
    </div>
  );
}

export default function OrderBook() {
  const fetcher = useCallback(() => api.krakenOrderbook(), []);
  const { data } = usePolling(fetcher, 5000);
  const bids = data?.bids || [];
  const asks = data?.asks || [];

  const { maxBidVol, maxAskVol, cumBids, cumAsks } = useMemo(() => {
    let mb = 0, ma = 0;
    const cb = [], ca = [];
    let runB = 0, runA = 0;
    for (const [, v] of bids) { runB += v; cb.push(runB); if (v > mb) mb = v; }
    for (const [, v] of asks) { runA += v; ca.push(runA); if (v > ma) ma = v; }
    return { maxBidVol: mb, maxAskVol: ma, cumBids: cb, cumAsks: ca };
  }, [bids, asks]);

  const maxCum = Math.max(
    cumBids.length ? cumBids[cumBids.length - 1] : 0,
    cumAsks.length ? cumAsks[cumAsks.length - 1] : 0,
  ) || 1;

  const rows = Math.min(10, Math.max(bids.length, asks.length));

  return (
    <div className="panel panel-orderbook">
      <div className="name">
        <span>order book</span>
        <span className="muted">DOGUSD · Kraken</span>
      </div>
      {bids.length === 0 && asks.length === 0 ? (
        <div className="value muted">loading</div>
      ) : (
        <div className="ob-wrap">
          <div className="ob-header">
            <span>bid</span>
            <span>price</span>
            <span>ask</span>
          </div>
          {Array.from({ length: rows }).map((_, i) => {
            const bid = bids[i];
            const ask = asks[i];
            const bidCum = cumBids[i] || 0;
            const askCum = cumAsks[i] || 0;
            return (
              <div key={i} className="ob-row">
                <div className="ob-bid-side">
                  {bid ? (
                    <>
                      <DepthBar pct={(bidCum / maxCum) * 100} side="bid" />
                      <span className="ob-vol">{fmtVol(bid[1])}</span>
                    </>
                  ) : <span />}
                </div>
                <div className="ob-prices">
                  <span className="ob-bid-price">{bid ? bid[0].toFixed(6) : ""}</span>
                  <span className="ob-ask-price">{ask ? ask[0].toFixed(6) : ""}</span>
                </div>
                <div className="ob-ask-side">
                  {ask ? (
                    <>
                      <DepthBar pct={(askCum / maxCum) * 100} side="ask" />
                      <span className="ob-vol">{fmtVol(ask[1])}</span>
                    </>
                  ) : <span />}
                </div>
              </div>
            );
          })}
          <div className="ob-footer">
            <span className="ob-cum bid">{fmtVol(cumBids[cumBids.length - 1] || 0)} DOG</span>
            <span className="muted">depth</span>
            <span className="ob-cum ask">{fmtVol(cumAsks[cumAsks.length - 1] || 0)} DOG</span>
          </div>
        </div>
      )}
    </div>
  );
}
