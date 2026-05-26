import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

function fmtUsd(n) {
  if (!n && n !== 0) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtDog(n) {
  if (!n && n !== 0) return "—";
  return Math.round(n).toLocaleString();
}

function fmtBtc(n) {
  if (!n && n !== 0) return "—";
  if (n < 0.001) return `${Math.round(n * 1e8).toLocaleString()} sats`;
  return n.toFixed(6);
}

export default function TreasuryPanel() {
  const fetcher = useCallback(() => api.treasury(), []);
  const { data } = usePolling(fetcher, 15000);

  const oc = data?.onchain;
  const kr = data?.kraken_paper;
  const tot = data?.totals;

  return (
    <div className="panel panel-treasury">
      <div className="name">
        <span>foundation treasury</span>
        <span className="muted">cross venue</span>
      </div>
      {!data || data.error ? (
        <div className="value muted">{data?.error || "loading"}</div>
      ) : (
        <>
          <div className="treasury-total">
            <span className="treasury-usd">{fmtUsd(tot?.grand_total_usd)}</span>
            <span className="treasury-sub muted">across all venues</span>
          </div>

          <div className="treasury-venues">
            <div className="treasury-venue">
              <div className="treasury-venue-header">
                <span className="treasury-venue-label">Bitcoin L1</span>
                <span className="treasury-venue-val muted">{fmtUsd(oc?.total_usd)}</span>
              </div>
              <div className="treasury-row">
                <span className="treasury-k">DOG</span>
                <span className="treasury-v">{fmtDog(oc?.dog)}</span>
              </div>
              <div className="treasury-row">
                <span className="treasury-k">BTC</span>
                <span className="treasury-v">{fmtBtc(oc?.btc)}</span>
              </div>
            </div>

            <div className="treasury-venue">
              <div className="treasury-venue-header">
                <span className="treasury-venue-label">Kraken (paper)</span>
                <span className="treasury-venue-val muted">{fmtUsd(kr?.portfolio_value)}</span>
              </div>
              <div className="treasury-row">
                <span className="treasury-k">DOG</span>
                <span className="treasury-v">{fmtDog(kr?.dog)}</span>
              </div>
              <div className="treasury-row">
                <span className="treasury-k">USD</span>
                <span className="treasury-v">{fmtUsd(kr?.usd)}</span>
              </div>
              <div className="treasury-row">
                <span className="treasury-k">PnL</span>
                <span className="treasury-v" style={{ color: kr?.pnl_pct >= 0 ? "var(--orange)" : "var(--bad)" }}>
                  {kr?.pnl_pct >= 0 ? "+" : ""}{kr?.pnl_pct?.toFixed(3)}%
                </span>
              </div>
              <div className="treasury-row">
                <span className="treasury-k">trades</span>
                <span className="treasury-v">{kr?.total_trades}</span>
              </div>
            </div>
          </div>

          <div className="treasury-bottom">
            <div className="treasury-totals">
              <div className="treasury-row">
                <span className="treasury-k">total DOG</span>
                <span className="treasury-v treasury-highlight">{fmtDog(tot?.dog)}</span>
              </div>
              <div className="treasury-row">
                <span className="treasury-k">total BTC</span>
                <span className="treasury-v">{fmtBtc(tot?.btc)}</span>
              </div>
              <div className="treasury-row">
                <span className="treasury-k">USD cash</span>
                <span className="treasury-v">{fmtUsd(tot?.usd_cash)}</span>
              </div>
            </div>
            <div className="treasury-qr">
              <img src="/assets/branding/foundation-qr.png" alt="Foundation wallet QR" className="treasury-qr-img" />
              <div className="treasury-qr-label">Dog of Bitcoin Foundation</div>
              <div className="treasury-qr-sub">501(c)(3) non profit</div>
              <div className="treasury-qr-sub">100% community backed</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
