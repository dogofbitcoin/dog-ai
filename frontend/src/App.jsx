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

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <picture className="header-logo">
          <source srcSet="/assets/branding/logo.webp" type="image/webp" />
          <img src="/assets/branding/logo.png" alt="DOG Ai: Release The Kraken" className="header-logo-img" />
        </picture>
        <div className="version">v0.1.0 · paper trading</div>
      </header>

      <TreasuryPanel />

      <div className="agent-grid">
        <TraderPanel />
        <KrakenPanel />
        <AlphaPanel />
        <GeneralPanel />
      </div>

      <div className="bottom-strip">
        <div className="bottom-left">
          <WhatToWatch />
          <ArbPanel />
        </div>
        <div className="bottom-right">
          <HealthBar />
          <div className="indicator-strip">
            <SpreadPanel />
            <VwapPanel />
            <SignalQualityPanel />
            <OnchainHeatPanel />
          </div>
        </div>
      </div>

      <footer className="footer">
        $DOG rune on bitcoin, dogswap and kraken, read only. operator actions ship as dry run cli strings.
      </footer>
    </div>
  );
}
