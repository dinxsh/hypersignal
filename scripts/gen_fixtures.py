"""Generate the recorded GoldRush fixtures used by --offline mode and tests.

These mirror the real GoldRush response shapes (Foundational log events and
Hyperliquid Info API payloads) with realistic-but-synthetic values, so the
demo runs deterministically without an API key. Re-run after changing the
scenario:  python scripts/gen_fixtures.py
"""
from __future__ import annotations

import json
from pathlib import Path

from hypersignal.config import RAY
from hypersignal.lending import RESERVE_DATA_UPDATED_TOPIC

OUT = Path(__file__).resolve().parents[1] / "src" / "hypersignal" / "fixtures"


def word(n: int) -> str:
    return f"{n:064x}"


def topic_addr(addr: str) -> str:
    return "0x" + "0" * 24 + addr.lower().replace("0x", "")


def reserve_event(reserve: str, supply_pct: float, borrow_pct: float, block: int, ts: str) -> dict:
    liq = int(supply_pct / 100 * RAY)
    var_borrow = int(borrow_pct / 100 * RAY)
    data = "0x" + word(liq) + word(0) + word(var_borrow) + word(10**27) + word(10**27)
    return {
        "block_signed_at": ts,
        "block_height": block,
        "tx_hash": "0x" + word(block)[:64],
        "raw_log_topics": [RESERVE_DATA_UPDATED_TOPIC, topic_addr(reserve)],
        "raw_log_data": data,
        "decoded": None,  # exercise the raw-decoding path
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # --- Use case 1: HyperLend ReserveDataUpdated events --------------------
    wHYPE = "0x5555555555555555555555555555555555555555"
    USDe = "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"
    USDT0 = "0xB8CE59FC3717ada4C02eaDF9682A9e934F625ebb"
    lending_events = [
        # stale wHYPE update -- should be overridden by the later block
        reserve_event(wHYPE, 2.9, 5.2, 9_000_000, "2026-06-29T00:00:00Z"),
        reserve_event(wHYPE, 3.4, 6.1, 9_050_000, "2026-06-30T11:00:00Z"),
        reserve_event(USDe, 8.2, 11.5, 9_050_100, "2026-06-30T11:05:00Z"),
        reserve_event(USDT0, 6.5, 9.0, 9_050_200, "2026-06-30T11:06:00Z"),
    ]

    # --- Use case 2: market context + whale state --------------------------
    meta_and_ctxs = [
        {"universe": [{"name": "BTC"}, {"name": "ETH"}, {"name": "HYPE"}]},
        [
            {"markPx": "94000.0", "funding": "0.0000100", "openInterest": "12000.0", "dayNtlVlm": "900000000.0"},
            {"markPx": "3300.0", "funding": "0.0000090", "openInterest": "80000.0", "dayNtlVlm": "500000000.0"},
            {"markPx": "38.5", "funding": "0.0000125", "openInterest": "5200000.0", "dayNtlVlm": "210000000.0"},
        ],
    ]

    def pos(coin, szi, pv, liq_px):
        return {"position": {"coin": coin, "szi": str(szi), "positionValue": str(pv), "liquidationPx": str(liq_px)}}

    batch_state = [
        {"user": "0xb0a55f13d22f66e6d495ac98113841b2326e9540", "assetPositions": [pos("HYPE", 100000, 3850000, 34.0)]},
        {"user": "0x31ca8395cf837de08b24da3f660e77761dfb974b", "assetPositions": [pos("HYPE", 50000, 1925000, 36.0)]},  # near liq
        {"user": "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00", "assetPositions": [pos("HYPE", -20000, 770000, 44.0)]},
        {"error": "upstream_error", "user": "0x73f9c53a8b15e43056d5599f6488ac9a8730f85d", "message": "overall batch timeout exceeded"},
    ]

    # --- Use case 3: ledger updates (deposits / withdrawals) ---------------
    def upd(t, usd, time_ms, h):
        return {"time": time_ms, "hash": h, "delta": {"type": t, "usdc": str(usd)}}

    ledger_updates = {
        "0xb0a55f13d22f66e6d495ac98113841b2326e9540": [
            upd("deposit", 1500000, 1782900000000, "0xaaa1"),
            upd("deposit", 5000, 1782900100000, "0xaaa2"),  # below threshold -> ignored
        ],
        "0x31ca8395cf837de08b24da3f660e77761dfb974b": [
            upd("deposit", 800000, 1782901000000, "0xbbb1"),
        ],
        "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00": [
            upd("withdraw", 400000, 1782902000000, "0xccc1"),
        ],
        "0x73f9c53a8b15e43056d5599f6488ac9a8730f85d": [],
    }

    for name, payload in {
        "lending_events.json": lending_events,
        "meta_and_asset_ctxs.json": meta_and_ctxs,
        "batch_clearinghouse_state.json": batch_state,
        "ledger_updates.json": ledger_updates,
    }.items():
        (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
