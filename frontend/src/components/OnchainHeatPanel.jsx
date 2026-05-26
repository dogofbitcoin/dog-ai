import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";
import { useSparkline } from "../hooks/useSparkline.js";
import Sparkline from "./Sparkline.jsx";

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
  const history = useSparkline(v?.score);

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="name">
        <span data-tip="how lit the on chain DOG pool is right now. blends fill rate, tvl, and trade velocity into one 0 to 100 score. high heat means buyers are active, low means quiet.">onchain heat</span>
        <span className="muted">DOG rune</span>
      </div>
      {!v ? (
        <div className="value muted">{env?.meta?.notes || "no data"}</div>
      ) : (
        <>
          <div className="value-row">
            <div className="value">{v.score.toFixed(1)}</div>
            <Sparkline data={history} color="#f7931a" />
          </div>
          <div className="bar"><span style={{ width: `${Math.min(100, v.score)}%` }} /></div>
          <div className="row"><span className="k" data-tip="how often DogSwap fills are landing. faster fills push this up.">fill rate</span><span>{v.components.fill_rate}</span></div>
          <div className="row"><span className="k" data-tip="how much DOG liquidity is parked in the pool. deeper pool, higher score.">tvl</span><span>{v.components.tvl}</span></div>
          <div className="row"><span className="k" data-tip="how much volume is turning relative to pool size. high velocity means the pool is moving.">velocity</span><span>{v.components.velocity}</span></div>
          <div className="row"><span className="k">fills 1h</span><span>{v.raw.fill_count_1h}</span></div>
          <div className="row"><span className="k">pool tvl</span><span>{fmtTvl(v.raw.tvl_dog)} DOG</span></div>
          {env.meta.notes ? <div className="sub">{env.meta.notes}</div> : null}
        </>
      )}
    </div>
  );
}
