const BASE = "/assets/agents/dog-of-bitcoin/actions";

export const poses = {
  REVIEWING_ALPHA:  `${BASE}/dog_of_bitcoin_reviewing_alpha_research.png`,
  LISTENING_GENERAL:`${BASE}/dog_of_bitcoin_listening_general_ghost.png`,
  WATCHING:         `${BASE}/dog_of_bitcoin_watching_state.png`,
  STEADY:           `${BASE}/dog_of_bitcoin_steady_state.png`,
  ATTENTIVE:        `${BASE}/dog_of_bitcoin_attentive_state.png`,
  NOD:              `${BASE}/dog_of_bitcoin_nod_approval.png`,
  HOLD:             `${BASE}/dog_of_bitcoin_hold_decision.png`,
  COMMUNITY:        `${BASE}/dog_of_bitcoin_community_voice.png`,
  SOVEREIGN_DESK:   `${BASE}/dog_of_bitcoin_sovereign_desk_pose.png`,
};

export const defaultPose = "SOVEREIGN_DESK";

export function pickPose(envelope) {
  if (!envelope) return defaultPose;

  const stance = envelope.stance;
  const t = envelope.trader || {};
  const intent = t.current_intent || {};
  const action = (intent.action || "").toLowerCase();
  const reasoning = (intent.reasoning || "").toLowerCase();
  const log = t.decision_log || [];
  const lastResult = log[0]?.result?.status;

  if (stance === "halted") return "STEADY";
  if (stance === "idle" && !t.initialised) return "SOVEREIGN_DESK";

  if (lastResult === "filled" && log[0]) {
    const fillAge = Date.now() / 1000 - (log[0].ts || 0);
    if (fillAge < 90) return "NOD";
  }

  if (reasoning.includes("accumul") || reasoning.includes("dca") || reasoning.includes("community"))
    return "COMMUNITY";

  if (reasoning.includes("signal") || reasoning.includes("quality") || reasoning.includes("alpha"))
    return "REVIEWING_ALPHA";

  if (reasoning.includes("heat") || reasoning.includes("onchain") || reasoning.includes("trend"))
    return "LISTENING_GENERAL";

  if (action === "hold") return "HOLD";
  if (action === "buy" || action === "sell") return "ATTENTIVE";

  if (stance === "trading") return "WATCHING";

  return "SOVEREIGN_DESK";
}
