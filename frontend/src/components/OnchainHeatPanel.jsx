import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

export default function OnchainHeatPanel() {
  const fetcher = useCallback(() => api.indicator("onchain_heat"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const v = env?.value;
  const stale = env?.meta?.stale;

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="name">
        <span>onchain heat</span>
        <span className="muted">DOG rune</span>
      </div>
      {!v ? (
        <div className="value muted">{env?.meta?.notes || "no data"}</div>
      ) : (
        <>
          <div className="value">{v.score.toFixed(1)}</div>
          <div className="bar"><span style={{ width: `${Math.min(100, v.score)}%` }} /></div>
          <div className="row"><span className="k">fill rate</span><span>{v.components.fill_rate}</span></div>
          <div className="row"><span className="k">holders</span><span>{v.components.holder}</span></div>
          <div className="row"><span className="k">velocity</span><span>{v.components.velocity}</span></div>
          <div className="row"><span className="k">fills 1h</span><span>{v.raw.fill_count_1h}</span></div>
          <div className="row"><span className="k">holder count</span><span>{v.raw.holder_count.toLocaleString()}</span></div>
          {env.meta.notes ? <div className="sub">{env.meta.notes}</div> : null}
        </>
      )}
    </div>
  );
}
