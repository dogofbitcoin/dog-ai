import { useState, useCallback } from "react";
import HealthBar from "./components/HealthBar.jsx";
import SpreadPanel from "./components/SpreadPanel.jsx";
import VwapPanel from "./components/VwapPanel.jsx";
import SignalQualityPanel from "./components/SignalQualityPanel.jsx";
import OnchainHeatPanel from "./components/OnchainHeatPanel.jsx";
import AlphaPanel from "./components/AlphaPanel.jsx";
import GeneralPanel from "./components/GeneralPanel.jsx";
import TraderPanel from "./components/TraderPanel.jsx";
import KrakenPanel from "./components/KrakenPanel.jsx";
import WhatToWatch from "./components/WhatToWatch.jsx";
import ArbPanel from "./components/ArbPanel.jsx";
import TreasuryPanel from "./components/TreasuryPanel.jsx";

function Spot({ id, label, active, onToggle, children }) {
  return (
    <div
      className={`spotlight-wrap${active === id ? " spot-on" : ""}${active && active !== id ? " spot-dim" : ""}`}
      onClick={(e) => {
        if (e.target.closest("button, a, input, select")) return;
        onToggle(id);
      }}
    >
      {active === id && <div className="spot-label">{label}</div>}
      {children}
    </div>
  );
}

export default function App() {
  const [spot, setSpot] = useState(null);
  const toggle = useCallback((id) => setSpot((prev) => (prev === id ? null : id)), []);

  return (
    <div className={`app${spot ? " spotlight-active" : ""}`}>
      <header className="header">
        <picture className="header-logo">
          <source srcSet="/assets/branding/logo.webp" type="image/webp" />
          <img src="/assets/branding/logo.png" alt="DOG Ai: Release The Kraken" className="header-logo-img" />
        </picture>
        <div className="version">v0.1.0 · paper trading</div>
      </header>

      <Spot id="treasury" label="Foundation Treasury" active={spot} onToggle={toggle}>
        <TreasuryPanel />
      </Spot>

      <div className="agent-grid">
        <Spot id="trader" label="Dog of Bitcoin" active={spot} onToggle={toggle}>
          <TraderPanel />
        </Spot>
        <Spot id="kraken" label="Kraken Agent" active={spot} onToggle={toggle}>
          <KrakenPanel />
        </Spot>
        <Spot id="alpha" label="Alpha" active={spot} onToggle={toggle}>
          <AlphaPanel />
        </Spot>
        <Spot id="general" label="General Ghost" active={spot} onToggle={toggle}>
          <GeneralPanel />
        </Spot>
      </div>

      <div className="bottom-strip">
        <div className="bottom-left">
          <Spot id="watch" label="What to Watch" active={spot} onToggle={toggle}>
            <WhatToWatch />
          </Spot>
          <Spot id="arb" label="Arb Spread" active={spot} onToggle={toggle}>
            <ArbPanel />
          </Spot>
        </div>
        <div className="bottom-right">
          <Spot id="health" label="System Health" active={spot} onToggle={toggle}>
            <HealthBar />
          </Spot>
          <Spot id="indicators" label="Indicators" active={spot} onToggle={toggle}>
            <div className="indicator-strip">
              <SpreadPanel />
              <VwapPanel />
              <SignalQualityPanel />
              <OnchainHeatPanel />
            </div>
          </Spot>
        </div>
      </div>

      <footer className="footer">
        $DOG rune on bitcoin, dogswap and kraken, read only. operator actions ship as dry run cli strings.
      </footer>
    </div>
  );
}
