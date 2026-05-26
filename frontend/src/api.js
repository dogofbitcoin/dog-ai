const BASE = import.meta.env.VITE_API_BASE || "/api";

async function getJson(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return res.json();
}

async function postJson(path) {
  const res = await fetch(`${BASE}${path}`, { method: "POST" });
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return res.json();
}

export const api = {
  health: () => getJson("/health/providers"),
  indicators: () => getJson("/indicators"),
  indicator: (name) => getJson(`/indicators/${name}`),
  agents: () => getJson("/agents"),
  agent: (name) => getJson(`/agents/${name}`),
  strategies: () => getJson("/agents/trader/strategies"),
  setStrategy: (name) => postJson(`/agents/trader/strategy?name=${encodeURIComponent(name)}`),
  treasury: () => getJson("/treasury"),
  dryRun: ({ side, volume, price, pair, orderType }) => {
    const params = new URLSearchParams({ side, volume: String(volume) });
    if (price != null) params.set("price", String(price));
    if (pair) params.set("pair", pair);
    if (orderType) params.set("order_type", orderType);
    return getJson(`/kraken/dry-run?${params.toString()}`);
  },
};
