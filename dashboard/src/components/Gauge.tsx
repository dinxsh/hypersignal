import { motion } from "framer-motion";

// Semicircle dial for directional bias in [-1, 1].
// -1 points left (coral / bearish), +1 points right (mint / bullish).
export function Gauge({ value }: { value: number }) {
  const v = Math.max(-1, Math.min(1, value));
  const cx = 100;
  const cy = 100;
  const r = 82;
  const needleAngle = 90 * (1 - v); // deg, measured CCW from +x axis
  const rad = (needleAngle * Math.PI) / 180;
  const nx = cx + (r - 14) * Math.cos(rad);
  const ny = cy - (r - 14) * Math.sin(rad);

  const ticks = [-1, -0.5, 0, 0.5, 1].map((t) => {
    const a = ((90 * (1 - t)) * Math.PI) / 180;
    return {
      x1: cx + (r + 2) * Math.cos(a),
      y1: cy - (r + 2) * Math.sin(a),
      x2: cx + (r + 9) * Math.cos(a),
      y2: cy - (r + 9) * Math.sin(a),
    };
  });

  return (
    <svg viewBox="0 0 200 118" width="200" height="118" role="img" aria-label={`directional bias ${v}`}>
      <defs>
        <linearGradient id="arcg" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#ff6a5a" />
          <stop offset="50%" stopColor="#7f909d" />
          <stop offset="100%" stopColor="#4df7cb" />
        </linearGradient>
      </defs>
      {/* track */}
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none"
        stroke="#1a2530"
        strokeWidth="12"
        strokeLinecap="round"
      />
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none"
        stroke="url(#arcg)"
        strokeWidth="3"
        strokeLinecap="round"
        opacity="0.85"
      />
      {ticks.map((t, i) => (
        <line key={i} x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} stroke="#4a5763" strokeWidth="1.5" />
      ))}
      {/* needle */}
      <motion.line
        x1={cx}
        y1={cy}
        x2={nx}
        y2={ny}
        stroke={v >= 0.05 ? "#4df7cb" : v <= -0.05 ? "#ff6a5a" : "#e9f1f4"}
        strokeWidth="3"
        strokeLinecap="round"
        initial={{ x2: cx, y2: cy - (r - 14) }}
        animate={{ x2: nx, y2: ny }}
        transition={{ type: "spring", stiffness: 90, damping: 14, delay: 0.25 }}
        style={{ filter: "drop-shadow(0 0 5px rgba(77,247,203,0.45))" }}
      />
      <circle cx={cx} cy={cy} r="6" fill="#0d141a" stroke="#4a5763" strokeWidth="1.5" />
      {/* denomination so the −1..+1 scale reads as bearish..bullish */}
      <text x="14" y="114" fontSize="8.5" fontFamily="var(--font-mono)" letterSpacing="0.5" fill="#ff6a5a">
        BEARISH −1
      </text>
      <text x="100" y="13" textAnchor="middle" fontSize="8" fontFamily="var(--font-mono)" letterSpacing="1" fill="#7f909d">
        NEUTRAL 0
      </text>
      <text x="186" y="114" textAnchor="end" fontSize="8.5" fontFamily="var(--font-mono)" letterSpacing="0.5" fill="#4df7cb">
        +1 BULLISH
      </text>
    </svg>
  );
}
