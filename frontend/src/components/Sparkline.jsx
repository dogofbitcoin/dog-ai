import { useId } from "react";

export default function Sparkline({ data, width = 80, height = 22, color = "#f7931a", strokeWidth = 1.5 }) {
  const id = useId();

  if (!data || data.length < 2) {
    return <svg width={width} height={height} className="sparkline" aria-hidden="true" />;
  }

  const pad = 2;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const stepX = width / (data.length - 1);

  const pts = data.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / span) * (height - pad * 2) - pad;
    return [x, y];
  });

  const line = pts.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
  const areaPath = `M${pts[0][0]},${pts[0][1]} ` +
    pts.slice(1).map(([x, y]) => `L${x},${y}`).join(" ") +
    ` L${pts[pts.length - 1][0]},${height} L${pts[0][0]},${height} Z`;

  const [lastX, lastY] = pts[pts.length - 1];

  return (
    <svg width={width} height={height} className="sparkline" aria-hidden="true">
      <defs>
        <linearGradient id={`${id}-fill`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
        <filter id={`${id}-glow`}>
          <feGaussianBlur stdDeviation="1.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <path d={areaPath} fill={`url(#${id}-fill)`} />
      <polyline
        points={line}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        filter={`url(#${id}-glow)`}
      />
      <circle cx={lastX} cy={lastY} r="2.5" fill={color} className="spark-dot" />
    </svg>
  );
}
