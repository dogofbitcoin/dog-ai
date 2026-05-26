import * as dogOfBitcoin from "./dogOfBitcoin.js";
import * as generalGhost from "./generalGhost.js";
import * as alpha from "./alpha.js";
import * as kraken from "./kraken.js";

const registry = {
  trader: dogOfBitcoin,
  general: generalGhost,
  alpha: alpha,
  kraken: kraken,
};

export function getPoseUrl(agentName, envelope) {
  const agent = registry[agentName];
  if (!agent) return null;
  const poseKey = agent.pickPose(envelope);
  return agent.poses[poseKey] || null;
}

export function getDefaultPoseUrl(agentName) {
  const agent = registry[agentName];
  if (!agent) return null;
  return agent.poses[agent.defaultPose] || null;
}

export function hasPoses(agentName) {
  return agentName in registry;
}
