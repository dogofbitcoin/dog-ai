import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

const STANCE_COLOR = {
  bullish: "#f7931a",
  neutral: "#ffb35e",
  bearish: "#c084fc",
};

export default function GeneralPanel() {
  const fetcher = useCallback(() => api.agent("general"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const stale = env?.meta?.stale;
  const color = STANCE_COLOR[env?.stance] || "#7a7088";

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="name">
        <span>agent general ghost</span>
        <span className="muted">directional</span>
      </div>
      {!env ? (
        <div className="value muted">no data</div>
      ) : (
        <>
          <div className="value" style={{ color }}>{env.stance}</div>
          <div className="bar">
            <span style={{ width: `${Math.min(100, env.confidence)}%`, background: color }} />
          </div>
          <div className="row"><span className="k">confidence</span><span>{env.confidence}</span></div>
          <div className="sub">{env.reasoning}</div>
        </>
      )}
    </div>
  );
}
