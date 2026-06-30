import { motion } from "framer-motion";
import type { RegimeSignal } from "../types";
import { decide } from "../decide";
import { price, fundingHourly, usdCompact } from "../format";
import { Gauge } from "./Gauge";

function biasClass(regime: string): string {
  const bias = regime.split("/")[0].trim().toLowerCase();
  if (bias === "risk-on") return "riskon";
  if (bias === "risk-off") return "riskoff";
  return "neutral";
}

function volColor(v: number): string {
  if (v >= 0.6) return "var(--coral)";
  if (v >= 0.35) return "var(--amber)";
  return "var(--mint)";
}

export function RegimeHero({ signal, markPrice }: { signal: RegimeSignal; markPrice: number }) {
  const directive = decide(signal);
  const actClass = `act-${directive.action.replace("-", "")}`;

  return (
    <>
      <motion.div
        className="hero"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* verdict */}
        <div className="verdict">
          <div className="kicker">Regime · {signal.coin}-PERP</div>
          <div className="regime">
            <span className={biasClass(signal.regime)}>{signal.regime}</span>
          </div>
          <div className="statline">
            <div className="row">
              <span className="k">mark</span>
              <span className="v">{price(markPrice)}</span>
            </div>
            <div className="row">
              <span className="k">funding</span>
              <span className="v" style={{ color: signal.funding_rate >= 0 ? "var(--mint)" : "var(--coral)" }}>
                {fundingHourly(signal.funding_rate)}
              </span>
            </div>
            <div className="row">
              <span className="k">HYPE borrow APR</span>
              <span className="v">{signal.hype_borrow_apr != null ? `${signal.hype_borrow_apr.toFixed(2)}%` : "—"}</span>
            </div>
            <div className="row">
              <span className="k">net 24h flow</span>
              <span className="v" style={{ color: signal.net_flow_usd >= 0 ? "var(--mint)" : "var(--coral)" }}>
                {signal.net_flow_usd >= 0 ? "+" : ""}
                {usdCompact(signal.net_flow_usd)}
              </span>
            </div>
          </div>
        </div>

        {/* gauges */}
        <div className="gauges">
          <Gauge value={signal.directional_bias} />
          <div className="gauge-readout">
            <div className="big" style={{ color: signal.directional_bias >= 0 ? "var(--mint)" : "var(--coral)" }}>
              {signal.directional_bias >= 0 ? "+" : ""}
              {signal.directional_bias.toFixed(2)}
            </div>
            <div className="lbl">directional bias</div>
          </div>
          <div className="volbar-wrap">
            <div className="volbar">
              <motion.div
                className="fill"
                style={{ background: volColor(signal.volatility_score) }}
                initial={{ width: 0 }}
                animate={{ width: `${signal.volatility_score * 100}%` }}
                transition={{ duration: 0.9, delay: 0.3, ease: "easeOut" }}
              />
            </div>
            <div className="volbar-legend">
              <span>VOLATILITY {(signal.volatility_score * 100).toFixed(0)}/100</span>
              <span>calm · choppy · turbulent</span>
            </div>
          </div>
        </div>

        {/* directive */}
        <div className="directive">
          <div className="kicker">Agent directive</div>
          <div>
            <div className={`action ${actClass}`}>{directive.action}</div>
            <div className="reason">{directive.reason}</div>
          </div>
          <span className="tag">derived for HYPE vault allocation</span>
        </div>
      </motion.div>

      {/* drivers */}
      <motion.div
        className="drivers"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        {signal.drivers.map((d, i) => (
          <span className="d" key={i}>
            {d}
          </span>
        ))}
      </motion.div>
    </>
  );
}
