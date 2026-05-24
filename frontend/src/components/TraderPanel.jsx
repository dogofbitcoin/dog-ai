import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

const STANCE_COLOR = {
  trading: "#f7931a",
  idle: "#7a7088",
  halted: "#e85a8a",
};

const ACTION_COLOR = {
  buy: "#f7931a",
  sell: "#c084fc",
  hold: "#7a7088",
  strategy_change: "#ffb35e",
};

function fmtAgo(ts) {
  if (!ts) return "never";
  const s = Math.floor(Date.now() / 1000 - ts);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

function fmtUsd(n) {
  if (n === undefined || n === null) return "—";
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function fmtNum(n, d = 0) {
  if (n === undefined || n === null) return "—";
  return n.toLocaleString(undefined, { maximumFractionDigits: d });
}

export default function TraderPanel() {
  const fetcher = useCallback(() => api.agent("trader"), []);
  const { data } = usePolling(fetcher, 5000);
  const [strategies, setStrategies] = useState([]);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    api.strategies().then((r) => setStrategies(r.strategies || [])).catch(() => {});
  }, []);

  const env = data?.envelope;
  const t = env?.trader;
  const color = STANCE_COLOR[env?.stance] || "#7a7088";

  const onPickStrategy = async (name) => {
    if (switching || name === t?.strategy?.active) return;
    setSwitching(true);
    try {
      await api.setStrategy(name);
    } finally {
      setSwitching(false);
    }
  };

  if (!t) {
    return (
      <div className="panel panel-wide">
        <div className="name"><span>agent dog of bitcoin <span className="muted">main character</span></span><span className="muted">loading</span></div>
        <div className="value muted">loading...</div>
      </div>
    );
  }

  const usd = t.balance?.USD?.total ?? 0;
  const dog = t.balance?.DOG?.total ?? 0;
  const value = t.portfolio?.current_value ?? 0;
  const pnlPct = t.portfolio?.unrealized_pnl_pct ?? 0;
  const trades = t.portfolio?.total_trades ?? 0;
  const log = t.decision_log || [];
  const active = t.strategy?.active;

  return (
    <div className="panel panel-wide">
      <div className="name">
        <span>agent dog of bitcoin <span className="muted">main character</span></span>
        <span style={{ color }}>{env.stance}</span>
      </div>

      {!t.configured ? (
        <div className="value muted">ANTHROPIC_API_KEY not set</div>
      ) : (
        <>
          <div className="strategy-bar">
            {strategies.map((s) => {
              const isActive = s.name === active;
              return (
                <button
                  key={s.name}
                  className={`strat-btn${isActive ? " active" : ""}`}
                  disabled={switching}
                  onClick={() => onPickStrategy(s.name)}
                  title={`${s.description}\n\nKraken CLI: ${s.kraken_emphasis}\nmax ${s.max_trade_dog} DOG/cycle · cooldown ${s.cooldown_s}s`}
                >
                  {s.title}
                </button>
              );
            })}
          </div>
          <div className="sub strategy-detail">
            {t.strategy?.description} <span className="muted">— {t.strategy?.kraken_emphasis}</span>
          </div>

          <div className="trader-row">
            <div className="metric"><div className="k">portfolio</div><div className="v">{fmtUsd(value)}</div></div>
            <div className="metric"><div className="k">pnl</div><div className="v" style={{ color: pnlPct >= 0 ? "#f7931a" : "#e85a8a" }}>{pnlPct.toFixed(2)}%</div></div>
            <div className="metric"><div className="k">cash</div><div className="v">{fmtUsd(usd)}</div></div>
            <div className="metric"><div className="k">dog held</div><div className="v">{fmtNum(dog, 0)}</div></div>
            <div className="metric"><div className="k">trades</div><div className="v">{trades}</div></div>
            <div className="metric"><div className="k">cycles</div><div className="v">{t.cycle_count}</div></div>
            <div className="metric"><div className="k">last decision</div><div className="v">{fmtAgo(t.last_decision_ts)}</div></div>
            <div className="metric"><div className="k">last fill</div><div className="v">{fmtAgo(t.last_fill_ts)}</div></div>
          </div>

          {env.meta?.notes ? <div className="sub" style={{ color: "#e85a8a" }}>{env.meta.notes}</div> : null}

          <div className="trader-current">
            <span className="k">current intent: </span>
            {t.current_intent ? (
              <>
                <span style={{ color: ACTION_COLOR[t.current_intent.action] || "#7a7088" }}>
                  {t.current_intent.action.toUpperCase()} {fmtNum(t.current_intent.size_dog, 0)} DOG
                </span>
                <span className="muted"> — {t.current_intent.reasoning}</span>
              </>
            ) : (
              <span className="muted">(awaiting first cycle)</span>
            )}
          </div>

          <div className="log-header">decision log</div>
          <div className="log">
            {log.length === 0 ? (
              <div className="muted">no decisions yet</div>
            ) : (
              log.slice(0, 12).map((entry, i) => {
                const d = entry.decision || {};
                const r = entry.result || {};
                const aColor = ACTION_COLOR[d.action] || "#7a7088";
                return (
                  <div key={i} className="log-entry">
                    <span className="log-time">{fmtAgo(entry.ts)}</span>
                    <span className="log-action" style={{ color: aColor }}>
                      {d.action?.toUpperCase()} {d.size_dog ? fmtNum(d.size_dog, 0) : ""}
                    </span>
                    <span className="log-status muted">[{r.status || "—"}]</span>
                    <span className="log-reason">{d.reasoning}</span>
                  </div>
                );
              })
            )}
          </div>
          <div className="sub muted">
            paper mode · max {fmtNum(t.config.max_trade_dog, 0)} DOG/cycle · cooldown {t.config.cooldown_s}s ·
            model {t.config.model}
          </div>
        </>
      )}
    </div>
  );
}
