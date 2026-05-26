const BASE = "/assets/agents/alpha/actions";

export const poses = {
  CONFIRMING_SIGNAL:    `${BASE}/alpha_confirming_signal_quality.png`,
  READING_MARKET:       `${BASE}/alpha_reading_market_data.png`,
  CALCULATING_VWAP:     `${BASE}/alpha_calculating_vwap.png`,
  CHECKING_DEPTH:       `${BASE}/alpha_checking_order_book_depth.png`,
  CROSS_REF_RUNE:       `${BASE}/alpha_cross_referencing_rune_data.png`,
  FLAGGING_SLIPPAGE:    `${BASE}/alpha_flagging_slippage_risk.png`,
  PULLING_TICKER:       `${BASE}/alpha_pulling_kraken_cli_ticker.png`,
  QUIET_DESK:           `${BASE}/alpha_quiet_research_desk_pose.png`,
  REVIEWING_OHLC:       `${BASE}/alpha_reviewing_ohlc_chart.png`,
};

export const defaultPose = "QUIET_DESK";

export function pickPose(envelope) {
  if (!envelope) return defaultPose;

  const stance = envelope.stance;
  const confidence = envelope.confidence ?? 0;
  const reasoning = (envelope.reasoning || "").toLowerCase();

  if (reasoning.includes("depth"))
    return "CHECKING_DEPTH";

  if (reasoning.includes("vwap"))
    return "CALCULATING_VWAP";

  if (reasoning.includes("agreement") && reasoning.includes("freshness"))
    return "CROSS_REF_RUNE";

  if (stance === "confident") {
    if (confidence > 70) return "CONFIRMING_SIGNAL";
    return "READING_MARKET";
  }

  if (stance === "tentative") {
    if (reasoning.includes("depth"))
      return "CHECKING_DEPTH";
    if (reasoning.includes("freshness"))
      return "FLAGGING_SLIPPAGE";
    return "REVIEWING_OHLC";
  }

  if (stance === "blind") {
    if (reasoning.includes("stale") || reasoning.includes("missing"))
      return "FLAGGING_SLIPPAGE";
    return "PULLING_TICKER";
  }

  return defaultPose;
}
