import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";
import Tabs from "./Tabs.jsx";
import CharacterAvatar from "./CharacterAvatar.jsx";

const STANCE_COLOR = {
  "tight-book": "#f7931a",
  "wide-book": "#c084fc",
  "low-signal": "#ffb35e",
  watching: "#7a7088",
};

function fmtAgo(ts) {
  if (!ts) return "never";
  const s = Math.floor(Date.now() / 1000 - ts);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

function fmtSatsFromBtc(btc) {
  if (btc === null || btc === undefined) return "—";
  return `${(btc * 1e8).toFixed(3)} sats`;
}

function fmtUsd(n) {
  if (n === null || n === undefined) return "—";
  return n.toFixed(6);
}

function TickerTab({ k }) {
  const synth = k.ticker.synthetic_dogbtc;
  const dogusd = k.ticker.dogusd;
  return (
    <div className="kraken-grid">
      <div className="kraken-block">
        <div className="block-title">DOGUSD (direct)</div>
        {dogusd?.available ? (
          <>
            <div className="kv"><span className="k">bid</span><span>{fmtUsd(dogusd.bid)}</span></div>
            <div className="kv"><span className="k">ask</span><span>{fmtUsd(dogusd.ask)}</span></div>
            <div className="kv"><span className="k">last</span><span>{fmtUsd(dogusd.last)}</span></div>
            <div className="kv"><span className="k">vol 24h</span><span>{(dogusd.volume_24h || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></div>
          </>
        ) : <div className="muted">unavailable</div>}
      </div>

      <div className="kraken-block">
        <div className="block-title">DOGBTC (synthetic)</div>
        {synth?.available ? (
          <>
            <div className="kv"><span className="k">bid</span><span>{fmtSatsFromBtc(synth.bid)}</span></div>
            <div className="kv"><span className="k">ask</span><span>{fmtSatsFromBtc(synth.ask)}</span></div>
            <div className="kv"><span className="k">last</span><span>{fmtSatsFromBtc(synth.last)}</span></div>
            <div className="sub muted">from DOGUSD / XBTUSD</div>
          </>
        ) : <div className="muted">unavailable</div>}
      </div>
    </div>
  );
}

function SkillTab({ k }) {
  return (
    <div className="kraken-block">
      <div className="block-title">skill in focus</div>
      <div className="skill-name">{k.skill_in_focus?.name}</div>
      <div className="skill-summary">{k.skill_in_focus?.summary}</div>
    </div>
  );
}

function shortCmd(cmd) {
  if (!cmd) return "";
  return cmd.replace(/\/home\/[^\s]+\/kraken/, "kraken");
}

function CliTab({ k }) {
  const lastCmd = k.last_fill_command;
  const dry = k.dry_run_preview || {};
  return (
    <>
      <div className="kraken-cmds">
        <div className="block-title">last fill</div>
        {lastCmd ? (
          <>
            <div className="cli">{shortCmd(lastCmd.command)}</div>
            <div className="sub muted">{fmtAgo(lastCmd.ts)}</div>
          </>
        ) : (
          <div className="muted">no fills yet</div>
        )}
      </div>
      <div className="kraken-cmds">
        <div className="block-title">dry run preview</div>
        <div className="cli">{shortCmd(dry.buy_2000_at_bid)}</div>
        <div className="cli">{shortCmd(dry.sell_2000_at_ask)}</div>
      </div>
    </>
  );
}

export default function KrakenPanel() {
  const fetcher = useCallback(() => api.agent("kraken"), []);
  const { data } = usePolling(fetcher, 5000);
  const env = data?.envelope;
  const k = env?.kraken;
  const stale = env?.meta?.stale;
  const color = STANCE_COLOR[env?.stance] || "#7a7088";

  if (!k) {
    return (
      <div className="panel panel-wide">
        <div className="panel-hero">
          <CharacterAvatar name="kraken" stance="watching" size={90} />
          <div className="panel-hero-text">
            <div className="name"><span>Kraken</span><span className="muted">exchange specialist</span></div>
            <div className="value muted">loading...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`panel panel-wide ${stale ? "stale" : ""}`}>
      <div className="panel-hero">
        <CharacterAvatar name="kraken" stance={env.stance} envelope={env} size={90} />
        <div className="panel-hero-text">
          <div className="name">
            <span>Kraken <span className="muted">exchange specialist</span></span>
            <span className="stance-pill" style={{ color, borderColor: color }}>
              <span className="pulse-dot" style={{ background: color }} />
              {env.stance}
            </span>
          </div>
        </div>
      </div>

      <Tabs
        tabs={[
          { id: "ticker", label: "ticker", render: () => <TickerTab k={k} /> },
          { id: "skill", label: "skill", render: () => <SkillTab k={k} /> },
          { id: "cli", label: "cli", render: () => <CliTab k={k} /> },
        ]}
      />
    </div>
  );
}
