import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";
import { useSparkline } from "../hooks/useSparkline.js";
import Sparkline from "./Sparkline.jsx";
import Tabs from "./Tabs.jsx";
import CharacterAvatar from "./CharacterAvatar.jsx";

const STANCE_COLOR = {
  bullish: "#f7931a",
  neutral: "#ffb35e",
  bearish: "#c084fc",
};

function OverviewTab({ env, color }) {
  return (
    <>
      <div className="row">
        <span className="k" data-tip="how strongly General Ghost believes in the current directional call. 0 to 100.">confidence</span>
        <span style={{ color }}>{env.confidence.toFixed(1)}%</span>
      </div>
      <div className="bar">
        <span style={{ width: `${Math.min(100, env.confidence)}%`, background: color }} />
      </div>
      <div className="sub">{env.reasoning}</div>
    </>
  );
}

function HeatTab({ ind }) {
  const v = ind?.envelope?.value;
  const score = v?.score;
  const history = useSparkline(score);
  if (!v) return <div className="muted">loading</div>;
  const c = v.components || {};
  const raw = v.raw || {};

  const scoreColor = score >= 65 ? "#f7931a" : score >= 35 ? "#ffb35e" : "#c084fc";
  return (
    <>
      <div className="value-row">
        <div className="value" style={{ color: scoreColor }}>{score?.toFixed(1)}</div>
        <Sparkline data={history} color={scoreColor} width={100} height={28} />
      </div>
      <div className="bar">
        <span style={{ width: `${Math.min(100, score || 0)}%`, background: scoreColor }} />
      </div>
      <div className="component-row" style={{ marginTop: 8 }}>
        <div className="component-item">
          <div className="component-label" data-tip="how often DogSwap fills are landing. faster fills push this up.">fill rate</div>
          <div className="component-value">{c.fill_rate ?? "—"}</div>
          <div className="component-bar"><span style={{ width: `${Math.min(100, c.fill_rate || 0)}%` }} /></div>
        </div>
        <div className="component-item">
          <div className="component-label" data-tip="how much DOG liquidity is in the pool. scored 0 to 100.">tvl score</div>
          <div className="component-value">{c.tvl ?? "—"}</div>
          <div className="component-bar"><span style={{ width: `${Math.min(100, c.tvl || 0)}%` }} /></div>
        </div>
        <div className="component-item">
          <div className="component-label" data-tip="volume relative to pool size. high velocity means active trading.">velocity</div>
          <div className="component-value">{c.velocity ?? "—"}</div>
          <div className="component-bar"><span style={{ width: `${Math.min(100, c.velocity || 0)}%` }} /></div>
        </div>
      </div>
      <div className="row" style={{ marginTop: 6 }}>
        <span className="k">fills 1h</span>
        <span>{raw.fill_count_1h ?? "—"}</span>
      </div>
    </>
  );
}

function SpreadTab({ ind }) {
  const v = ind?.envelope?.value;
  const history = useSparkline(v?.spread_bps);
  if (!v) return <div className="muted">loading</div>;

  const bpsColor = v.spread_bps > 80 ? "#c084fc" : v.spread_bps < 25 ? "#f7931a" : "#ffb35e";
  return (
    <>
      <div className="value-row">
        <div className="value" style={{ color: bpsColor }}>{v.spread_bps.toFixed(1)} bps</div>
        <Sparkline data={history} color={bpsColor} width={100} height={28} />
      </div>
      <div className="row"><span className="k">bid</span><span>{(v.bid * 1e8).toFixed(3)} sats</span></div>
      <div className="row"><span className="k">ask</span><span>{(v.ask * 1e8).toFixed(3)} sats</span></div>
      <div className="row"><span className="k">mid</span><span>{(v.mid * 1e8).toFixed(3)} sats</span></div>
      <div className="sub muted" style={{ marginTop: 6 }}>
        {v.spread_bps > 80 ? "wide book, liquidity is thin" :
         v.spread_bps < 25 ? "tight book, cheap to trade" :
         "moderate spread, normal conditions"}
      </div>
    </>
  );
}

export default function GeneralPanel() {
  const fetcher = useCallback(() => api.agent("general"), []);
  const heatFetcher = useCallback(() => api.indicator("onchain_heat"), []);
  const spreadFetcher = useCallback(() => api.indicator("spread"), []);
  const { data } = usePolling(fetcher, 5000);
  const { data: heatInd } = usePolling(heatFetcher, 5000);
  const { data: spreadInd } = usePolling(spreadFetcher, 5000);
  const env = data?.envelope;
  const stale = env?.meta?.stale;
  const color = STANCE_COLOR[env?.stance] || "#7a7088";

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="panel-hero">
        <CharacterAvatar name="general" stance={env?.stance || "neutral"} envelope={env} size={90} />
        <div className="panel-hero-text">
          <div className="name">
            <span>General Ghost <span className="muted">directional</span></span>
            {env && (
              <span className="stance-pill" style={{ color, borderColor: color }}>
                <span className="pulse-dot" style={{ background: color }} />
                {env.stance}
              </span>
            )}
          </div>
        </div>
      </div>
      {!env ? (
        <div className="value muted">no data</div>
      ) : (
        <Tabs tabs={[
          { id: "overview", label: "overview", render: () => <OverviewTab env={env} color={color} /> },
          { id: "heat", label: "heat", render: () => <HeatTab ind={heatInd} /> },
          { id: "spread", label: "spread", render: () => <SpreadTab ind={spreadInd} /> },
        ]} />
      )}
    </div>
  );
}
