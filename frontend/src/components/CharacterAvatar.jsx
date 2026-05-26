import { useState, useEffect, useRef } from "react";
import { getPoseUrl, hasPoses } from "../poses/index.js";

function DogOfBitcoin() {
  return (
    <svg viewBox="0 0 64 64" className="avatar-svg" aria-hidden="true">
      <defs>
        <radialGradient id="dog-glow" cx="50%" cy="50%" r="55%">
          <stop offset="0%" stopColor="#f7931a" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#f7931a" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="url(#dog-glow)" />
      <path d="M14 22 L20 14 L24 24 Z" fill="#c46a00" />
      <path d="M50 22 L44 14 L40 24 Z" fill="#c46a00" />
      <circle cx="32" cy="34" r="18" fill="#f7931a" />
      <ellipse cx="25" cy="32" rx="2.4" ry="3" fill="#1d1530" />
      <ellipse cx="39" cy="32" rx="2.4" ry="3" fill="#1d1530" />
      <ellipse cx="32" cy="42" rx="5" ry="3.5" fill="#c46a00" />
      <circle cx="32" cy="40" r="1.4" fill="#0d0814" />
      <text x="32" y="22" textAnchor="middle" fontSize="7" fontWeight="700" fill="#0d0814" fontFamily="ui-monospace">B</text>
    </svg>
  );
}

function Alpha() {
  return (
    <svg viewBox="0 0 64 64" className="avatar-svg" aria-hidden="true">
      <defs>
        <radialGradient id="alpha-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#ffb35e" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#ffb35e" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="url(#alpha-glow)" />
      <path d="M28 10 L20 36 L29 36 L23 54 L42 28 L33 28 L38 10 Z" fill="#f7931a" stroke="#ffb35e" strokeWidth="1.2" strokeLinejoin="round" />
    </svg>
  );
}

function GeneralGhost() {
  return (
    <svg viewBox="0 0 64 64" className="avatar-svg" aria-hidden="true">
      <defs>
        <radialGradient id="ghost-glow" cx="50%" cy="50%" r="55%">
          <stop offset="0%" stopColor="#c084fc" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#c084fc" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="url(#ghost-glow)" />
      <path
        d="M16 30 C16 18 22 12 32 12 C42 12 48 18 48 30 L48 52 L43 48 L38 52 L32 48 L26 52 L21 48 L16 52 Z"
        fill="#8b5cf6"
        stroke="#c084fc"
        strokeWidth="1.2"
      />
      <circle cx="26" cy="28" r="2.5" fill="#f8f8ff" />
      <circle cx="38" cy="28" r="2.5" fill="#f8f8ff" />
      <circle cx="26" cy="28" r="1.2" fill="#1d1530" />
      <circle cx="38" cy="28" r="1.2" fill="#1d1530" />
      <rect x="28" y="36" width="8" height="2" fill="#c084fc" />
      <rect x="29" y="40" width="6" height="1.5" fill="#c084fc" />
    </svg>
  );
}

function Kraken() {
  return (
    <svg viewBox="0 0 64 64" className="avatar-svg" aria-hidden="true">
      <defs>
        <radialGradient id="kraken-glow" cx="50%" cy="50%" r="55%">
          <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="kraken-body" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#c084fc" />
          <stop offset="100%" stopColor="#6d28d9" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="url(#kraken-glow)" />
      <ellipse cx="32" cy="26" rx="14" ry="12" fill="url(#kraken-body)" stroke="#c084fc" strokeWidth="1" />
      <path d="M18 30 Q14 38 18 48 Q22 44 20 36" fill="none" stroke="#8b5cf6" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M46 30 Q50 38 46 48 Q42 44 44 36" fill="none" stroke="#8b5cf6" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M26 36 Q24 46 28 52" fill="none" stroke="#8b5cf6" strokeWidth="2" strokeLinecap="round" />
      <path d="M38 36 Q40 46 36 52" fill="none" stroke="#8b5cf6" strokeWidth="2" strokeLinecap="round" />
      <path d="M32 36 Q32 48 32 54" fill="none" stroke="#8b5cf6" strokeWidth="2" strokeLinecap="round" />
      <circle cx="32" cy="24" r="5" fill="#f8f8ff" />
      <circle cx="32" cy="24" r="2.4" fill="#1d1530" />
      <path d="M18 18 L24 14 L28 18" fill="none" stroke="#f7931a" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M36 18 L40 14 L46 18" fill="none" stroke="#f7931a" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

const SVG_RENDERERS = {
  trader: DogOfBitcoin,
  alpha: Alpha,
  general: GeneralGhost,
  kraken: Kraken,
};

const ANIMATION_CLASS = {
  trader: {
    trading: "anim-bounce",
    idle: "anim-breath",
    halted: "anim-droop",
  },
  alpha: {
    confident: "anim-pulse",
    tentative: "anim-flicker",
    blind: "anim-dim",
  },
  general: {
    bullish: "anim-float",
    neutral: "anim-breath",
    bearish: "anim-sink",
  },
  kraken: {
    "tight-book": "anim-pulse",
    "wide-book": "anim-sway",
    "low-signal": "anim-dim",
    watching: "anim-breath",
  },
};

function PoseImage({ src, alt, size }) {
  const [loaded, setLoaded] = useState(false);
  const [errored, setErrored] = useState(false);
  const prevSrc = useRef(src);
  const prevLoaded = useRef(null);

  useEffect(() => {
    if (src !== prevSrc.current) {
      if (loaded) prevLoaded.current = prevSrc.current;
      prevSrc.current = src;
      setLoaded(false);
      setErrored(false);
    }
  }, [src, loaded]);

  if (errored) return null;

  return (
    <div className="pose-container" style={{ width: size, height: size }}>
      {prevLoaded.current && !loaded && (
        <img
          src={prevLoaded.current}
          alt=""
          className="pose-img pose-img-prev"
          style={{ width: size, height: size }}
        />
      )}
      <img
        src={src}
        alt={alt}
        className={`pose-img ${loaded ? "pose-img-visible" : "pose-img-loading"}`}
        style={{ width: size, height: size }}
        onLoad={() => {
          setLoaded(true);
          prevLoaded.current = null;
        }}
        onError={() => setErrored(true)}
      />
    </div>
  );
}

export default function CharacterAvatar({ name, stance, envelope, size = 64 }) {
  const poseUrl = hasPoses(name) ? getPoseUrl(name, envelope) : null;
  const [poseAvailable, setPoseAvailable] = useState(null);
  const checkedUrls = useRef(new Set());

  useEffect(() => {
    if (!poseUrl) { setPoseAvailable(false); return; }
    if (checkedUrls.current.has(poseUrl)) return;
    const img = new Image();
    img.onload = () => { checkedUrls.current.add(poseUrl); setPoseAvailable(true); };
    img.onerror = () => { checkedUrls.current.add(poseUrl); setPoseAvailable(false); };
    img.src = poseUrl;
  }, [poseUrl]);

  if (poseAvailable && poseUrl) {
    return (
      <div className="avatar" style={{ width: size, height: size }}>
        <PoseImage src={poseUrl} alt={name} size={size} />
      </div>
    );
  }

  const Renderer = SVG_RENDERERS[name];
  if (!Renderer) return null;
  const animClass = ANIMATION_CLASS[name]?.[stance] || "anim-breath";
  return (
    <div className={`avatar ${animClass}`} style={{ width: size, height: size }}>
      <Renderer />
    </div>
  );
}
