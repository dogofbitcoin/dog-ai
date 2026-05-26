import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";
import CharacterAvatar from "./CharacterAvatar.jsx";

const DISPLAY = {
  trader: { display: "Dog of Bitcoin", role: "main character" },
  kraken: { display: "Kraken", role: "exchange specialist" },
  alpha: { display: "Alpha", role: "data confidence" },
  general: { display: "General Ghost", role: "directional" },
};

const STANCE_COLOR = {
  trading: "#f7931a",
  idle: "#7a7088",
  halted: "#e85a8a",
  confident: "#f7931a",
  tentative: "#ffb35e",
  blind: "#7a7088",
  bullish: "#f7931a",
  neutral: "#ffb35e",
  bearish: "#c084fc",
  "tight-book": "#f7931a",
  "wide-book": "#c084fc",
  "low-signal": "#ffb35e",
  watching: "#7a7088",
};

const ORDER = ["trader", "kraken", "alpha", "general"];

export default function CharacterStrip() {
  const fetcher = useCallback(() => api.agents(), []);
  const { data } = usePolling(fetcher, 5000);

  const byName = {};
  for (const a of data?.agents || []) {
    byName[a.name] = a.envelope;
  }

  return (
    <div className="character-strip">
      {ORDER.map((name) => {
        const env = byName[name];
        const stance = env?.stance || "idle";
        const meta = DISPLAY[name];
        const color = STANCE_COLOR[stance] || "#7a7088";
        return (
          <div key={name} className="character-card">
            <CharacterAvatar name={name} stance={stance} envelope={env} size={80} />
            <div className="character-info">
              <div className="character-name">{meta.display}</div>
              <div className="character-role">{meta.role}</div>
              <div className="character-stance" style={{ color, borderColor: color }}>
                <span className="pulse-dot" style={{ background: color }} />
                {stance}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
