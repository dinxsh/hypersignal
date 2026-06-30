import { motion } from "framer-motion";
import type { PriceSeries } from "../types";
import { price, signedPct } from "../format";
import { Panel } from "./Panel";

// SVG area chart for HYPE OHLCV (close line + filled gradient).
export function PriceChart({ data }: { data: PriceSeries }) {
  const cs = data.candles;
  const W = 720;
  const H = 230;
  const pad = 6;

  let path = "";
  let area = "";
  if (cs.length > 1) {
    const closes = cs.map((c) => c.c);
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const span = max - min || 1;
    const x = (i: number) => pad + (i / (cs.length - 1)) * (W - 2 * pad);
    const y = (v: number) => pad + (1 - (v - min) / span) * (H - 2 * pad);
    path = closes.map((v, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(" ");
    area = `${path} L ${x(cs.length - 1).toFixed(1)} ${H - pad} L ${x(0).toFixed(1)} ${H - pad} Z`;
  }

  const up = data.change_pct >= 0;
  const stroke = up ? "var(--mint)" : "var(--coral)";

  return (
    <Panel
      title={`${data.coin} Price · 72h`}
      sub={`${data.interval} candles · live OHLCV`}
      endpoint="Info · candleSnapshot"
      delay={0.1}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginBottom: 6 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em" }}>
          {price(data.last)}
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 15, color: stroke }}>{signedPct(data.change_pct)}</span>
        <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--faint)" }}>
          H {price(data.high)} · L {price(data.low)}
        </span>
      </div>

      {cs.length > 1 ? (
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none">
          <defs>
            <linearGradient id="pcfill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={up ? "rgba(77,247,203,0.28)" : "rgba(255,106,90,0.28)"} />
              <stop offset="100%" stopColor="rgba(0,0,0,0)" />
            </linearGradient>
          </defs>
          <path d={area} fill="url(#pcfill)" />
          <motion.path
            d={path}
            fill="none"
            stroke={stroke}
            strokeWidth="2"
            strokeLinejoin="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.1, ease: "easeOut" }}
          />
        </svg>
      ) : (
        <div className="note">no candle data</div>
      )}
    </Panel>
  );
}
