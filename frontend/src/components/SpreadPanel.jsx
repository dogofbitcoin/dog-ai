import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";
import { useSparkline } from "../hooks/useSparkline.js";
import Sparkline from "./Sparkline.jsx";

const fmtSats = (btcPrice) => (btcPrice * 1e8).toFixed(3);

export default function SpreadPanel() {
  const fetcher = useCallback(() => api.indicator("spread"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const v = env?.value;
  const stale = env?.meta?.stale;
  const history = useSparkline(v?.spread_bps);

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="name">
        <span data-tip="the gap between the best buy and best sell on Kraken, in basis points. tight means cheap to trade; wide means the book is thin or jittery.">spread</span>
        <span className="muted">{v?.pair || "..."}</span>
      </div>
      {!v ? (
        <div className="value muted">no data</div>
      ) : (
        <>
          <div className="value-row">
            <div className="value">{v.spread_bps.toFixed(1)} bps</div>
            <Sparkline data={history} color="#f7931a" />
          </div>
          <div className="row"><span className="k">bid</span><span>{fmtSats(v.bid)} sats</span></div>
          <div className="row"><span className="k">ask</span><span>{fmtSats(v.ask)} sats</span></div>
          <div className="row"><span className="k">mid</span><span>{fmtSats(v.mid)} sats</span></div>
          {v.synthetic ? <div className="sub">synthesised from DOGUSD and XBTUSD</div> : null}
          {env.meta.notes ? <div className="sub">{env.meta.notes}</div> : null}
        </>
      )}
    </div>
  );
}
