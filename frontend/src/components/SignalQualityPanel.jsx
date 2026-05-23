import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

export default function SignalQualityPanel() {
  const fetcher = useCallback(() => api.indicator("signal_quality"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const v = env?.value;
  const stale = env?.meta?.stale;

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="name">
        <span>signal quality</span>
        <span className="muted">0 to 100</span>
      </div>
      {!v ? (
        <div className="value muted">{env?.meta?.notes || "no data"}</div>
      ) : (
        <>
          <div className="value">{v.score.toFixed(1)}</div>
          <div className="bar green"><span style={{ width: `${Math.min(100, v.score)}%` }} /></div>
          <div className="row"><span className="k">freshness</span><span>{v.components.freshness}</span></div>
          <div className="row"><span className="k">depth</span><span>{v.components.depth}</span></div>
          <div className="row"><span className="k">agreement</span><span>{v.components.agreement}</span></div>
          <div className="row"><span className="k">age</span><span>{v.age_seconds}s</span></div>
          {env.meta.notes ? <div className="sub">{env.meta.notes}</div> : null}
        </>
      )}
    </div>
  );
}
