import type { RegimeSignal } from "./types";

export interface Directive {
  action: "ADD" | "HOLD" | "REDUCE" | "DE-RISK";
  reason: string;
}

// TS port of examples/agent_consumer.py:decide — the allocation directive an
// agent derives from the regime signal. This is the line Harmonix's vault
// agent acts on.
export function decide(s: RegimeSignal): Directive {
  if (s.volatility_score >= 0.6) {
    return { action: "DE-RISK", reason: "Turbulent regime — trim leverage and widen hedges." };
  }
  if (s.directional_bias >= 0.25 && s.volatility_score < 0.6) {
    if ((s.hype_borrow_apr ?? 0) < 12) {
      return { action: "ADD", reason: "Risk-on with workable lending carry." };
    }
    return { action: "HOLD", reason: "Risk-on, but HYPE borrow APR too rich to lever." };
  }
  if (s.directional_bias <= -0.25) {
    return { action: "REDUCE", reason: "Distribution / risk-off bias — rotate down exposure." };
  }
  return { action: "HOLD", reason: "Neutral regime — no allocation change." };
}
