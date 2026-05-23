import { useEffect, useRef, useState } from "react";

export function usePolling(fn, intervalMs = 5000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    let timer = null;

    const tick = async () => {
      try {
        const out = await fn();
        if (!cancelled.current) {
          setData(out);
          setError(null);
        }
      } catch (e) {
        if (!cancelled.current) setError(e.message || String(e));
      } finally {
        if (!cancelled.current) {
          setLoading(false);
          timer = setTimeout(tick, intervalMs);
        }
      }
    };

    tick();
    return () => {
      cancelled.current = true;
      if (timer) clearTimeout(timer);
    };
  }, [fn, intervalMs]);

  return { data, error, loading };
}
