"""Fuse the three modules into one HYPE regime signal.

The output is deliberately small and explainable -- a directional bias in
[-1, 1], a volatility score in [0, 1], a regime label, and a list of
plain-English drivers. That is the shape an allocation agent can act on
directly (size up, size down, hedge, sit out) without re-deriving anything.
"""
from __future__ import annotations

from pydantic import BaseModel

from .config import Settings, TARGET_COIN
from .flows import FlowSnapshot
from .lending import LendingSnapshot
from .whales import WhaleSnapshot


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


class RegimeSignal(BaseModel):
    coin: str
    directional_bias: float  # -1 (bearish) .. +1 (bullish)
    volatility_score: float  # 0 (calm) .. 1 (turbulent)
    regime: str
    drivers: list[str]
    # carried-through headline numbers an agent may want without re-reading
    hype_supply_apr: float | None = None
    hype_borrow_apr: float | None = None
    funding_rate: float = 0.0
    whale_skew: float = 0.0
    net_flow_usd: float = 0.0


def build_signal(
    lending: LendingSnapshot,
    whales: WhaleSnapshot,
    flows: FlowSnapshot,
    settings: Settings,
    coin: str = TARGET_COIN,
) -> RegimeSignal:
    drivers: list[str] = []

    hype = lending.by_symbol("wHYPE") or lending.by_symbol("HYPE")
    hype_borrow = hype.borrow_apr_pct if hype else 0.0
    hype_supply = hype.supply_apr_pct if hype else 0.0

    # --- directional bias ---------------------------------------------------
    flow_component = _clamp(flows.net_flow_usd / 2_000_000.0)
    whale_component = whales.skew
    directional = _clamp(0.6 * flow_component + 0.4 * whale_component)

    if flows.direction == "accumulation":
        drivers.append(f"net ${flows.net_flow_usd:,.0f} deposited into HyperCore (accumulation)")
    elif flows.direction == "distribution":
        drivers.append(f"net ${-flows.net_flow_usd:,.0f} withdrawn from HyperCore (distribution)")
    drivers.append(f"whale positioning {whales.positioning} (skew {whales.skew:+.2f})")

    # --- volatility score ---------------------------------------------------
    crowd = abs(whales.skew) if whales.crowded else abs(whales.skew) * 0.5
    near_liq_ratio = whales.near_liquidation / max(whales.wallets_with_position, 1)
    borrow_pressure = min(hype_borrow / 20.0, 1.0)  # 20%+ HYPE borrow APR == max leverage stress
    flow_mag = min(abs(flows.net_flow_usd) / 2_000_000.0, 1.0)
    volatility = round(
        max(0.0, min(1.0, 0.35 * crowd + 0.30 * near_liq_ratio + 0.20 * borrow_pressure + 0.15 * flow_mag)),
        3,
    )

    if whales.near_liquidation:
        drivers.append(f"{whales.near_liquidation} whale position(s) within {settings.thresholds.near_liq_pct:.0%} of liquidation")
    if hype_borrow:
        drivers.append(f"HYPE lending: {hype_supply:.2f}% supply / {hype_borrow:.2f}% borrow APR")
    if whales.market.funding_rate:
        drivers.append(f"funding {whales.market.funding_rate:+.4%}/hr")

    regime = _regime_label(directional, volatility)

    return RegimeSignal(
        coin=coin,
        directional_bias=round(directional, 3),
        volatility_score=volatility,
        regime=regime,
        drivers=drivers,
        hype_supply_apr=hype_supply or None,
        hype_borrow_apr=hype_borrow or None,
        funding_rate=whales.market.funding_rate,
        whale_skew=whales.skew,
        net_flow_usd=flows.net_flow_usd,
    )


def _regime_label(directional: float, volatility: float) -> str:
    vol = "turbulent" if volatility >= 0.6 else "choppy" if volatility >= 0.35 else "calm"
    if directional >= 0.25:
        bias = "risk-on"
    elif directional <= -0.25:
        bias = "risk-off"
    else:
        bias = "neutral"
    return f"{bias} / {vol}"
