import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

const fmtTvl = (dog) => {
  if (!dog) return "0";
  if (dog >= 1e9) return `${(dog / 1e9).toFixed(2)}B`;
  if (dog >= 1e6) return `${(dog / 1e6).toFixed(2)}M`;
  if (dog >= 1e3) return `${(dog / 1e3).toFixed(1)}K`;
  return dog.toFixed(0);
};

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
          <div className="row"><span className="k">tvl</span><span>{v.components.tvl}</span></div>
          <div className="row"><span className="k">velocity</span><span>{v.components.velocity}</span></div>
          <div className="row"><span className="k">fills 1h</span><span>{v.raw.fill_count_1h}</span></div>
          <div className="row"><span className="k">fills 24h</span><span>{v.raw.fill_count_24h}</span></div>
          <div className="row"><span className="k">pool tvl</span><span>{fmtTvl(v.raw.tvl_dog)} DOG</span></div>
          <div className="row"><span className="k">24h volume</span><span>{(v.raw.volume_24h_btc || 0).toFixed(4)} BTC</span></div>
          {env.meta.notes ? <div className="sub">{env.meta.notes}</div> : null}
        </>
      )}
    </div>
  );
}
