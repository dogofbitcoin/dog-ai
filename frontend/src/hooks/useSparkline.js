import { useEffect, useRef, useState } from "react";

export function useSparkline(value, max = 30) {
  const [history, setHistory] = useState([]);
  const lastRef = useRef(null);

  useEffect(() => {
    if (value === undefined || value === null || Number.isNaN(value)) return;
    if (lastRef.current === value) return;
    lastRef.current = value;
    setHistory((h) => {
      const next = [...h, value];
      if (next.length > max) next.shift();
      return next;
    });
  }, [value, max]);

  return history;
}
