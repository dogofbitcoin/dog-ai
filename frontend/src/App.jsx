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

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <div className="title">
          <span className="brand-dog">DOG</span>
          <span className="brand-ai"> Ai</span>
          <span className="brand-sep">:</span>
          <span className="brand-release"> Release The </span>
          <span className="brand-kraken">Kraken</span>
        </div>
        <div className="version">v0.1.0 · paper trading</div>
      </header>

      <HealthBar />

      <WhatToWatch />

      <div className="section-label">indicators</div>
      <div className="indicator-strip">
        <SpreadPanel />
        <VwapPanel />
        <SignalQualityPanel />
        <OnchainHeatPanel />
      </div>

      <div className="agents-row">
        <div>
          <div className="section-label">main character</div>
          <TraderPanel />
        </div>
        <div>
          <div className="section-label">exchange specialist</div>
          <KrakenPanel />
        </div>
      </div>

      <div className="section-label">supporting cast</div>
      <div className="support-row">
        <AlphaPanel />
        <GeneralPanel />
      </div>

      <footer className="footer">
        $DOG rune on bitcoin, dotswap and kraken, read only. operator actions ship as dry run cli strings.
      </footer>
    </div>
  );
}
