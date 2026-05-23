import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

const STANCE_COLOR = {
  confident: "#62b67a",
  tentative: "#e2bb53",
  blind: "#9a9a9a",
};

export default function AlphaPanel() {
  const fetcher = useCallback(() => api.agent("alpha"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const stale = env?.meta?.stale;
  const color = STANCE_COLOR[env?.stance] || "#9a9a9a";

  return (
    <div className={`panel ${stale ? "stale" : ""}`}>
      <div className="name">
        <span>agent alpha</span>
        <span className="muted">data confidence</span>
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
