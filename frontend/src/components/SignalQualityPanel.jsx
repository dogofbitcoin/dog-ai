import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";
import { useSparkline } from "../hooks/useSparkline.js";
import Sparkline from "./Sparkline.jsx";

export default function SignalQualityPanel() {
  const fetcher = useCallback(() => api.indicator("signal_quality"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const v = env?.value;
  const stale = env?.meta?.stale;
  const history = useSparkline(v?.score);

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="name">
        <span data-tip="how trustworthy the market data is right now. fresh quotes, deep book, and DEX vs CEX agreement all push this up. low quality means the agents will hold off.">signal quality</span>
        <span className="muted">0 to 100</span>
      </div>
      {!v ? (
        <div className="value muted">{env?.meta?.notes || "no data"}</div>
      ) : (
        <>
          <div className="value-row">
            <div className="value">{v.score.toFixed(1)}</div>
            <Sparkline data={history} color="#c084fc" />
          </div>
          <div className="bar green"><span style={{ width: `${Math.min(100, v.score)}%` }} /></div>
          <div className="row"><span className="k" data-tip="how recently the data updated. stale data drops this.">freshness</span><span>{v.components.freshness}</span></div>
          <div className="row"><span className="k" data-tip="how thick the order book is. thin books mean small trades move price.">depth</span><span>{v.components.depth}</span></div>
          <div className="row"><span className="k" data-tip="how closely the DogSwap and Kraken prices agree. divergence drops this.">agreement</span><span>{v.components.agreement}</span></div>
          <div className="row"><span className="k">age</span><span>{v.age_seconds}s</span></div>
          {env.meta.notes ? <div className="sub">{env.meta.notes}</div> : null}
        </>
      )}
    </div>
  );
}
