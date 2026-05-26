const BASE = "/assets/agents/general-ghost/actions";

export const poses = {
  PUSH:                `${BASE}/general_ghost_push_signal.png`,
  STRIKE:              `${BASE}/general_ghost_strike_signal.png`,
  POINTING:            `${BASE}/general_ghost_pointing_aggressively.png`,
  CORRECT_CALL:        `${BASE}/general_ghost_correct_call_celebration.png`,
  STAND:               `${BASE}/general_ghost_stand_signal.png`,
  REVIEWING_ONCHAIN:   `${BASE}/general_ghost_reviewing_onchain_data.png`,
  READING_ALPHA:       `${BASE}/general_ghost_reading_alpha_research.png`,
  FADE:                `${BASE}/general_ghost_fade_signal.png`,
  IMPATIENT:           `${BASE}/general_ghost_impatient_arms_crossed.png`,
};

export const defaultPose = "STAND";

export function pickPose(envelope) {
  if (!envelope) return defaultPose;

  const stance = envelope.stance;
  const confidence = envelope.confidence ?? 0;
  const reasoning = (envelope.reasoning || "").toLowerCase();

  if (reasoning.includes("alpha") || reasoning.includes("signal") || reasoning.includes("freshness"))
    return "READING_ALPHA";

  if (reasoning.includes("tvl") || reasoning.includes("fill rate") || reasoning.includes("velocity"))
    return "REVIEWING_ONCHAIN";

  if (stance === "bullish") {
    if (confidence > 70) return "PUSH";
    if (confidence > 40) return "POINTING";
    return "STRIKE";
  }

  if (stance === "bearish") {
    if (confidence > 50) return "FADE";
    return "IMPATIENT";
  }

  if (stance === "neutral") {
    if (reasoning.includes("wide book") || reasoning.includes("thin"))
      return "IMPATIENT";
    return "STAND";
  }

  return defaultPose;
}
