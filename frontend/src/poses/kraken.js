const BASE = "/assets/agents/kraken/actions";

export const poses = {
  ONLINE:              `${BASE}/kraken_online_status.png`,
  BUSY:                `${BASE}/kraken_busy_status.png`,
  SLOW:                `${BASE}/kraken_slow_status.png`,
  OFFLINE:             `${BASE}/kraken_offline_status.png`,
  CHECKING_LATENCY:    `${BASE}/kraken_checking_cli_latency.png`,
  DRY_RUN_DISPLAY:     `${BASE}/kraken_displaying_dry_run_cli_command.png`,
  INFRA_REPORT:        `${BASE}/kraken_infrastructure_status_report.png`,
  READY_EXECUTE:       `${BASE}/kraken_ready_to_execute_dry_run.png`,
  RECEIVING_APPROVAL:  `${BASE}/kraken_receiving_approval_signal.png`,
};

export const defaultPose = "ONLINE";

export function pickPose(envelope) {
  if (!envelope) return defaultPose;

  const stance = envelope.stance;
  const k = envelope.kraken || {};
  const reasoning = (envelope.reasoning || "").toLowerCase();
  const stale = envelope.meta?.stale;

  if (stale) return "OFFLINE";

  if (k.last_fill_command) {
    const fillAge = Date.now() / 1000 - (k.last_fill_command.ts || 0);
    if (fillAge < 120) return "RECEIVING_APPROVAL";
  }

  if (reasoning.includes("fee") || reasoning.includes("maker"))
    return "INFRA_REPORT";

  if (stance === "tight-book") {
    if (reasoning.includes("dca")) return "READY_EXECUTE";
    return "ONLINE";
  }

  if (stance === "wide-book") {
    if (reasoning.includes("slippage")) return "SLOW";
    return "BUSY";
  }

  if (stance === "low-signal") {
    return "CHECKING_LATENCY";
  }

  if (stance === "watching") {
    if (k.dry_run_preview) return "DRY_RUN_DISPLAY";
    return "ONLINE";
  }

  return defaultPose;
}
