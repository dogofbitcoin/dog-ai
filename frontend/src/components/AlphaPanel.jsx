import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";
import { useSparkline } from "../hooks/useSparkline.js";
import Sparkline from "./Sparkline.jsx";
import Tabs from "./Tabs.jsx";
import CharacterAvatar from "./CharacterAvatar.jsx";

const STANCE_COLOR = {
  confident: "#f7931a",
  tentative: "#ffb35e",
  blind: "#7a7088",
};

function OverviewTab({ env, color }) {
  return (
    <>
      <div className="row">
        <span className="k" data-tip="how much Alpha trusts the current data quality. 0 to 100.">confidence</span>
        <span style={{ color }}>{env.confidence.toFixed(1)}%</span>
      </div>
      <div className="bar green">
        <span style={{ width: `${Math.min(100, env.confidence)}%` }} />
      </div>
      <div className="sub">{env.reasoning}</div>
    </>
  );
}

function ComponentsTab({ ind }) {
  const v = ind?.envelope?.value;
  if (!v) return <div className="muted">loading</div>;
  const c = v.components || {};
  return (
    <>
      <div className="component-row">
        <div className="component-item">
          <div className="component-label" data-tip="how recently the data updated. stale data drops this.">freshness</div>
          <div className="component-value">{c.freshness ?? "—"}</div>
          <div className="component-bar"><span style={{ width: `${Math.min(100, c.freshness || 0)}%` }} /></div>
        </div>
        <div className="component-item">
          <div className="component-label" data-tip="how thick the order book is. thin books mean small trades move price.">depth</div>
          <div className="component-value">{c.depth ?? "—"}</div>
          <div className="component-bar"><span style={{ width: `${Math.min(100, c.depth || 0)}%` }} /></div>
        </div>
        <div className="component-item">
          <div className="component-label" data-tip="how closely the DogSwap and Kraken prices agree. divergence drops this.">agreement</div>
          <div className="component-value">{c.agreement ?? "—"}</div>
          <div className="component-bar"><span style={{ width: `${Math.min(100, c.agreement || 0)}%` }} /></div>
        </div>
      </div>
      <div className="row" style={{ marginTop: 8 }}>
        <span className="k">composite score</span>
        <span>{v.score?.toFixed(1) ?? "—"}</span>
      </div>
      <div className="row">
        <span className="k">data age</span>
        <span>{v.age_seconds ?? "—"}s</span>
      </div>
    </>
  );
}

function SignalTab({ ind }) {
  const v = ind?.envelope?.value;
  const score = v?.score;
  const history = useSparkline(score);
  if (!v) return <div className="muted">loading</div>;

  const scoreColor = score >= 70 ? "#f7931a" : score >= 30 ? "#ffb35e" : "#7a7088";
  return (
    <>
      <div className="value-row">
        <div className="value" style={{ color: scoreColor }}>{score?.toFixed(1)}</div>
        <Sparkline data={history} color={scoreColor} width={100} height={28} />
      </div>
      <div className="bar green">
        <span style={{ width: `${Math.min(100, score || 0)}%` }} />
      </div>
      <div className="sub muted" style={{ marginTop: 6 }}>
        {score >= 70 ? "data is reliable, agents can act with confidence" :
         score >= 30 ? "partial coverage, treat numbers as directional" :
         "data is missing or stale, agents will hold off"}
      </div>
    </>
  );
}

export default function AlphaPanel() {
  const fetcher = useCallback(() => api.agent("alpha"), []);
  const indFetcher = useCallback(() => api.indicator("signal_quality"), []);
  const { data } = usePolling(fetcher, 5000);
  const { data: ind } = usePolling(indFetcher, 5000);
  const env = data?.envelope;
  const stale = env?.meta?.stale;
  const color = STANCE_COLOR[env?.stance] || "#7a7088";

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="panel-hero">
        <CharacterAvatar name="alpha" stance={env?.stance || "blind"} envelope={env} size={90} />
        <div className="panel-hero-text">
          <div className="name">
            <span>Alpha <span className="muted">data confidence</span></span>
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
          { id: "components", label: "components", render: () => <ComponentsTab ind={ind} /> },
          { id: "signal", label: "signal", render: () => <SignalTab ind={ind} /> },
        ]} />
      )}
    </div>
  );
}
