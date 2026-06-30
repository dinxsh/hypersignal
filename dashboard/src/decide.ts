import type { RegimeSignal } from "./types";
import { usdCompact } from "./format";

export interface Directive {
  action: "ADD" | "HOLD" | "REDUCE" | "DE-RISK";
  context: string; // what it means for the HYPE vault, and why
}

// TS port of examples/agent_consumer.py:decide — the allocation directive an
// agent derives from the regime signal. `context` spells out the vault action
// and the trigger so the call isn't a bare verb.
export function decide(s: RegimeSignal): Directive {
  const bias = s.directional_bias.toFixed(2);
  const vol = Math.round(s.volatility_score * 100);
  const apr = (s.hype_borrow_apr ?? 0).toFixed(2);
  const flow = usdCompact(Math.abs(s.net_flow_usd));

  if (s.volatility_score >= 0.6) {
    return {
      action: "DE-RISK",
      context: `Turbulent regime (volatility ${vol}/100). Trim HYPE vault leverage, widen hedges, raise the stable buffer.`,
    };
  }
  if (s.directional_bias >= 0.25 && s.volatility_score < 0.6) {
    if ((s.hype_borrow_apr ?? 0) < 12) {
      return {
        action: "ADD",
        context: `Risk-on (bias +${bias}) and HYPE borrow APR ${apr}% leaves positive carry — scale HYPE exposure up.`,
      };
    }
    return {
      action: "HOLD",
      context: `Risk-on (bias +${bias}) but HYPE borrow APR ${apr}% is too rich to lever profitably — hold size.`,
    };
  }
  if (s.directional_bias <= -0.25) {
    return {
      action: "REDUCE",
      context: `Risk-off (bias ${bias}) with ${flow} net out of HyperCore — rotate HYPE down toward stables, cut leverage.`,
    };
  }
  return {
    action: "HOLD",
    context: `Mixed signals (bias ${bias}, volatility ${vol}/100) — keep the current allocation.`,
  };
}
