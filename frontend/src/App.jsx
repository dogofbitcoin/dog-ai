import HealthBar from "./components/HealthBar.jsx";
import SpreadPanel from "./components/SpreadPanel.jsx";
import VwapPanel from "./components/VwapPanel.jsx";
import SignalQualityPanel from "./components/SignalQualityPanel.jsx";
import OnchainHeatPanel from "./components/OnchainHeatPanel.jsx";
import AlphaPanel from "./components/AlphaPanel.jsx";
import GeneralPanel from "./components/GeneralPanel.jsx";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <div className="title">
          dog <b>of</b> bitcoin
        </div>
        <div className="version">v0.1.0 read only</div>
      </header>

      <HealthBar />

      <div className="section-label">agents</div>
      <div className="grid">
        <AlphaPanel />
        <GeneralPanel />
      </div>

      <div className="section-label">indicators</div>
      <div className="grid">
        <SpreadPanel />
        <VwapPanel />
        <SignalQualityPanel />
        <OnchainHeatPanel />
      </div>

      <footer className="footer">
        $DOG rune on bitcoin, dotswap and kraken, read only. operator actions ship as dry run cli strings.
      </footer>
    </div>
  );
}
