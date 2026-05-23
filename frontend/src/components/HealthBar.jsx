import { useCallback } from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

export default function HealthBar() {
  const fetcher = useCallback(() => api.health(), []);
  const { data, error } = usePolling(fetcher, 10000);

  if (error) {
    return <div className="health"><span className="pill bad">backend unreachable</span></div>;
  }
  if (!data) {
    return <div className="health"><span className="pill">loading</span></div>;
  }
  return (
    <div className="health">
      {data.providers.map((p) => (
        <span key={p.name} className={`pill ${p.ok ? "ok" : "bad"}`}>
          {p.name}: {p.ok ? "ok" : p.note || "down"}
          {p.ok && p.latency_ms ? ` (${p.latency_ms} ms)` : null}
        </span>
      ))}
    </div>
  );
}
