"""Minimal example: how an allocation agent consumes the regime signal.

This is the loop a yield agent (e.g. one allocating across HyperLend / Felix)
would run on a cron. Swap `offline=True` for a live key to go real-time.

    python examples/agent_consumer.py
"""
from __future__ import annotations

from hypersignal import Settings, run


def decide(report) -> str:
    """Turn a regime signal into a coarse allocation action."""
    s = report.signal
    if s.volatility_score >= 0.6:
        return "DE-RISK: turbulent regime, trim leverage and widen hedges"
    if s.directional_bias >= 0.25 and s.volatility_score < 0.6:
        # Risk-on but financeable only if HYPE borrow APR isn't eating the carry.
        if (s.hype_borrow_apr or 0) < 12:
            return "ADD: risk-on, lending carry is workable"
        return "HOLD: risk-on but HYPE borrow APR too rich to lever"
    if s.directional_bias <= -0.25:
        return "REDUCE: distribution / risk-off bias"
    return "HOLD: neutral regime"


def main() -> None:
    report = run(Settings.from_env(), offline=True)
    s = report.signal
    print(f"[{report.generated_at}] {s.coin} regime: {s.regime}")
    print(f"  directional_bias={s.directional_bias:+.3f}  volatility={s.volatility_score:.3f}")
    for d in s.drivers:
        print(f"  - {d}")
    print(f"\n  ACTION -> {decide(report)}")


if __name__ == "__main__":
    main()
