import * as dogOfBitcoin from "./dogOfBitcoin.js";

const registry = {
  trader: dogOfBitcoin,
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
