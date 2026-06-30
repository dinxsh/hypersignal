"""Use case 3 -- large stablecoin / HYPE flows in and out of HyperCore.

For each watched wallet we read ``userNonFundingLedgerUpdates`` (deposits,
withdrawals, transfers, vault flows) over a recent window and keep the events
whose USD value crosses the "large flow" threshold. Net deposits into HyperCore
read as accumulation / dry powder; net withdrawals read as de-risking or
rotation back to HyperEVM. This is the on-chain money-movement signal Harmonix
asked for -- "deposit and withdraw huge amounts of stablecoin / HYPE out of
hyperevm/hypercore and vice versa".

At firehose scale (every wallet, not a watchlist), the same data is available
as ``hl_deposits`` / ``hl_withdrawals`` tables via the GoldRush Pipeline API.
"""
from __future__ import annotations

import time

from pydantic import BaseModel

from .config import Settings

# Ledger delta types that represent value entering vs leaving HyperCore.
_INFLOW_TYPES = {"deposit"}
_OUTFLOW_TYPES = {"withdraw"}


def _f(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _delta_usd(delta: dict) -> float:
    """Best-effort USD value of a ledger delta."""
    for key in ("usdc", "usdcValue", "usdValue"):
        if key in delta:
            return _f(delta[key])
    return 0.0


class LargeFlow(BaseModel):
    wallet: str
    direction: str  # "in" (into HyperCore) | "out"
    type: str
    usd: float
    token: str
    time_ms: int
    hash: str | None = None


class FlowSnapshot(BaseModel):
    window_hours: int
    threshold_usd: float
    wallets_scanned: int
    inflow_usd: float
    outflow_usd: float
    net_flow_usd: float  # positive => net deposits into HyperCore
    large_event_count: int
    direction: str  # "accumulation" | "distribution" | "neutral"
    events: list[LargeFlow]


def parse_flows(
    updates_by_wallet: dict[str, list[dict]],
    settings: Settings,
) -> FlowSnapshot:
    th = settings.thresholds
    inflow = outflow = 0.0
    events: list[LargeFlow] = []

    for wallet, updates in updates_by_wallet.items():
        for upd in updates:
            delta = upd.get("delta", {})
            dtype = str(delta.get("type", "")).lower()
            usd = _delta_usd(delta)
            if usd < th.large_flow_usd:
                continue
            if dtype in _INFLOW_TYPES:
                inflow += usd
                direction = "in"
            elif dtype in _OUTFLOW_TYPES:
                outflow += usd
                direction = "out"
            else:
                continue
            events.append(
                LargeFlow(
                    wallet=wallet,
                    direction=direction,
                    type=dtype,
                    usd=round(usd, 2),
                    token=str(delta.get("token", "USDC")),
                    time_ms=int(upd.get("time", 0)),
                    hash=upd.get("hash"),
                )
            )

    net = inflow - outflow
    if net > th.large_flow_usd:
        label = "accumulation"
    elif net < -th.large_flow_usd:
        label = "distribution"
    else:
        label = "neutral"

    events.sort(key=lambda e: e.usd, reverse=True)
    return FlowSnapshot(
        window_hours=th.flow_lookback_hours,
        threshold_usd=th.large_flow_usd,
        wallets_scanned=len(updates_by_wallet),
        inflow_usd=round(inflow, 2),
        outflow_usd=round(outflow, 2),
        net_flow_usd=round(net, 2),
        large_event_count=len(events),
        direction=label,
        events=events,
    )


def fetch_flows(client, settings: Settings) -> FlowSnapshot:
    """Live fetch: ledger updates for every watched wallet over the window."""
    start_ms = int((time.time() - settings.thresholds.flow_lookback_hours * 3600) * 1000)
    updates_by_wallet: dict[str, list[dict]] = {}
    for wallet in settings.whale_watchlist:
        updates_by_wallet[wallet] = client.user_non_funding_ledger_updates(wallet, start_ms)
    return parse_flows(updates_by_wallet, settings)
