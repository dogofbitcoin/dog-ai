import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

const fmtSats = (btcPrice) => (btcPrice * 1e8).toFixed(3);

export default function VwapPanel() {
  const fetcher = useCallback(() => api.indicator("vwap"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const v = env?.value;
  const stale = env?.meta?.stale;

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="name">
        <span>vwap</span>
        <span className="muted">{v ? `${v.window_seconds}s` : "..."}</span>
      </div>
      {!v ? (
        <div className="value muted">{env?.meta?.notes || "no data"}</div>
      ) : (
        <>
          <div className="value">{fmtSats(v.vwap)} sats</div>
          <div className="row"><span className="k">samples</span><span>{v.samples}</span></div>
          <div className="row"><span className="k">pair</span><span>{v.pair}</span></div>
          {v.synthetic ? <div className="sub">prices converted to BTC via XBTUSD</div> : null}
        </>
      )}
    </div>
  );
}
