"""Use case 1 -- HyperEVM lending rates for HYPE and stablecoins.

HyperLend is an Aave v3 friendly-fork on HyperEVM. Its Pool emits
``ReserveDataUpdated`` on every supply/borrow/repay, and that event carries the
live ``liquidityRate`` (supply APR) and ``variableBorrowRate`` (borrow APR) in
RAY fixed-point. We pull those events from the GoldRush Foundational API,
decode them (whether GoldRush returns them decoded or raw), and keep the latest
update per reserve.

This gives an AI yield agent the exact lending rates it would otherwise scrape
from a few cron'd RPC calls -- but across the whole market in one request.
"""
from __future__ import annotations

from eth_utils import keccak
from pydantic import BaseModel

from .config import (
    HYPERLEND_POOL,
    RAY,
    RESERVE_DATA_UPDATED_SIG,
    RESERVES,
    Settings,
)
from .goldrush import FoundationalClient

# Pre-computed topic0 for the ReserveDataUpdated event signature.
RESERVE_DATA_UPDATED_TOPIC = "0x" + keccak(text=RESERVE_DATA_UPDATED_SIG).hex()


class ReserveRate(BaseModel):
    symbol: str
    reserve: str
    kind: str  # "native" | "stable" | "unknown"
    supply_apr_pct: float
    borrow_apr_pct: float
    block_height: int
    updated_at: str | None = None


class LendingSnapshot(BaseModel):
    market: str = "HyperLend"
    pool: str = HYPERLEND_POOL
    reserves: list[ReserveRate]

    def by_symbol(self, symbol: str) -> ReserveRate | None:
        return next((r for r in self.reserves if r.symbol.lower() == symbol.lower()), None)


def _word(data_hex: str, index: int) -> int:
    """Read the ``index``-th 32-byte word from ABI-packed event data as int."""
    raw = data_hex[2:] if data_hex.startswith("0x") else data_hex
    start = index * 64
    return int(raw[start : start + 64] or "0", 16)


def _reserve_meta(addr: str) -> dict:
    return RESERVES.get(addr.lower(), {"symbol": addr[:10], "kind": "unknown"})


def _rate_from_decoded(params: list[dict]) -> tuple[str, int, int]:
    """Pull (reserve, liquidityRate, variableBorrowRate) from GoldRush-decoded params."""
    by_name = {p["name"]: p["value"] for p in params}
    return (
        str(by_name["reserve"]),
        int(by_name["liquidityRate"]),
        int(by_name["variableBorrowRate"]),
    )


def _rate_from_raw(event: dict) -> tuple[str, int, int]:
    """Pull (reserve, liquidityRate, variableBorrowRate) from raw topics + data."""
    topics = event["raw_log_topics"]
    reserve = "0x" + topics[1][-40:]  # indexed address, right-aligned in the 32-byte topic
    data = event["raw_log_data"]
    return reserve, _word(data, 0), _word(data, 2)


def parse_lending(events: list[dict]) -> LendingSnapshot:
    """Build a LendingSnapshot from raw GoldRush log-event items.

    Keeps the most recent ReserveDataUpdated per reserve.
    """
    latest: dict[str, ReserveRate] = {}
    for ev in sorted(events, key=lambda e: e.get("block_height", 0)):
        decoded = ev.get("decoded")
        try:
            if decoded and decoded.get("name") == "ReserveDataUpdated":
                reserve, liq, borrow = _rate_from_decoded(decoded["params"])
            elif ev.get("raw_log_topics", [None])[0] == RESERVE_DATA_UPDATED_TOPIC:
                reserve, liq, borrow = _rate_from_raw(ev)
            else:
                continue
        except (KeyError, IndexError, TypeError, ValueError):
            continue

        meta = _reserve_meta(reserve)
        latest[reserve.lower()] = ReserveRate(
            symbol=meta["symbol"],
            reserve=reserve,
            kind=meta.get("kind", "unknown"),
            supply_apr_pct=round(liq / RAY * 100, 4),
            borrow_apr_pct=round(borrow / RAY * 100, 4),
            block_height=ev.get("block_height", 0),
            updated_at=ev.get("block_signed_at"),
        )

    reserves = sorted(latest.values(), key=lambda r: r.symbol)
    return LendingSnapshot(reserves=reserves)


def fetch_lending(client: FoundationalClient, settings: Settings) -> LendingSnapshot:
    """Live fetch: scan recent HyperLend Pool events and decode reserve rates."""
    events = client.log_events_by_contract(
        settings.chain_name,
        HYPERLEND_POOL,
        page_size=1000,
    )
    return parse_lending(events)
