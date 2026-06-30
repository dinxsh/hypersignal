"""Orchestration: wire the three modules into one report, live or offline.

``offline=True`` runs the exact same parsing/fusion code against recorded
GoldRush fixtures so the demo (and its tests) run deterministically without an
API key. ``offline=False`` hits the live GoldRush APIs using GOLDRUSH_API_KEY.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib import resources

from pydantic import BaseModel

from .config import Settings, TARGET_COIN
from .flows import FlowSnapshot, fetch_flows, parse_flows
from .goldrush import FoundationalClient, InfoClient
from .lending import LendingSnapshot, fetch_lending, parse_lending
from .signal import RegimeSignal, build_signal
from .whales import WhaleSnapshot, fetch_whales, parse_whales


class HyperSignalReport(BaseModel):
    generated_at: str
    mode: str  # "live" | "offline"
    signal: RegimeSignal
    lending: LendingSnapshot
    whales: WhaleSnapshot
    flows: FlowSnapshot


def _fixture(name: str):
    with resources.files("hypersignal.fixtures").joinpath(name).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(settings: Settings, *, offline: bool = False, coin: str = TARGET_COIN) -> HyperSignalReport:
    if offline:
        lending = parse_lending(_fixture("lending_events.json"))
        whales = parse_whales(
            _fixture("meta_and_asset_ctxs.json"),
            _fixture("batch_clearinghouse_state.json"),
            settings,
            coin,
        )
        flows = parse_flows(_fixture("ledger_updates.json"), settings)
    else:
        if not settings.api_key:
            raise RuntimeError(
                "GOLDRUSH_API_KEY is not set. Set it, or run with --offline to use recorded fixtures."
            )
        foundational = FoundationalClient(settings.api_key, base_url=settings.foundational_base_url)
        info = InfoClient(settings.api_key, base_url=settings.info_base_url)
        try:
            lending = fetch_lending(foundational, settings)
            whales = fetch_whales(info, settings, coin)
            flows = fetch_flows(info, settings)
        finally:
            foundational.close()
            info.close()

    signal = build_signal(lending, whales, flows, settings, coin)
    return HyperSignalReport(
        generated_at=_now_iso(),
        mode="offline" if offline else "live",
        signal=signal,
        lending=lending,
        whales=whales,
        flows=flows,
    )
