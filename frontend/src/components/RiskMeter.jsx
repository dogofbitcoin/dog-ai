function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n));
}

function pickColor(pct) {
  if (pct < 50) return "#f7931a";
  if (pct < 80) return "#ffb35e";
  return "#e85a8a";
}

function Gauge({ label, pct, valueLabel, tip }) {
  const color = pickColor(pct);
  return (
    <div className="gauge" data-tip={tip}>
      <div className="gauge-head">
        <span className="gauge-label">{label}</span>
        <span className="gauge-value" style={{ color }}>{valueLabel}</span>
      </div>
      <div className="gauge-track">
        <div className="gauge-fill" style={{ width: `${clamp(pct, 0, 100)}%`, background: color }} />
      </div>
    </div>
  );
}

export default function RiskMeter({ t }) {
  const dog = t.balance?.DOG?.total ?? 0;
  const positionCap = t.config?.max_position_dog ?? 50000;
  const positionPct = (dog / positionCap) * 100;

  const pnlPct = t.portfolio?.unrealized_pnl_pct ?? 0;
  const hardStop = t.config?.hard_stop_pct ?? 5;
  const drawdownPct = pnlPct >= 0 ? 0 : (Math.abs(pnlPct) / hardStop) * 100;

  const tradePerCycle = t.config?.max_trade_dog ?? 2000;
  const cooldown = t.config?.cooldown_s ?? 60;

  return (
    <div className="risk-meter">
      <div className="block-title">risk rails</div>
      <Gauge
        label="position cap"
        pct={positionPct}
        valueLabel={`${dog.toLocaleString(undefined, { maximumFractionDigits: 0 })} / ${positionCap.toLocaleString()} DOG`}
        tip="how much DOG Dog of Bitcoin can hold at once. orange is healthy, red means he is near the cap and will refuse to buy more."
      />
      <Gauge
        label="drawdown to halt"
        pct={drawdownPct}
        valueLabel={pnlPct >= 0 ? "clear" : `${Math.abs(pnlPct).toFixed(2)}% of ${hardStop}%`}
        tip="distance to the hard stop. if unrealized losses hit the halt threshold, Dog of Bitcoin stops trading until manually reset."
      />
      <div className="risk-detail">
        <span className="k">per cycle</span>
        <span>{tradePerCycle.toLocaleString()} DOG max · cooldown {cooldown}s</span>
      </div>
    </div>
  );
}
