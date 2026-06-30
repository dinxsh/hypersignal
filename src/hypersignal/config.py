"""Static configuration for hypersignal.

Everything an operator would tune lives here: the GoldRush endpoints, the
HyperEVM lending market being tracked, the reserve/token registry, the whale
watchlist, and the thresholds that turn raw on-chain data into signals.

Addresses below are HyperEVM mainnet (chain id 999) and were taken from the
HyperLend developer docs and HyperEVMScan. Swap the watchlist and thresholds
for your own; nothing here is secret.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

# --- GoldRush endpoints -----------------------------------------------------
# Foundational API (REST) for HyperEVM on-chain data.
FOUNDATIONAL_BASE_URL = "https://api.covalenthq.com/v1"
# Hyperliquid Info API: a drop-in replacement for api.hyperliquid.xyz/info
# with no rate limits. Used for HyperCore whale state and ledger flows.
INFO_BASE_URL = "https://hypercore.goldrushdata.com"

CHAIN_NAME = "hyperevm-mainnet"  # Foundational API chain slug for HyperEVM
CHAIN_ID = 999

# --- HyperEVM lending market (use case 1) -----------------------------------
# HyperLend is an Aave v3.0.2 friendly-fork. Its Pool emits ReserveDataUpdated
# on every interaction, carrying the live supply/borrow rates in RAY (1e27).
HYPERLEND_POOL = "0x00A89d7a5A02160f20150EbEA7a2b5E4879A1A8b"

# Aave v3 ReserveDataUpdated event:
#   ReserveDataUpdated(
#       address indexed reserve,
#       uint256 liquidityRate,        # supply APR, RAY
#       uint256 stableBorrowRate,     # RAY
#       uint256 variableBorrowRate,   # borrow APR, RAY
#       uint256 liquidityIndex,
#       uint256 variableBorrowIndex)
RESERVE_DATA_UPDATED_SIG = (
    "ReserveDataUpdated(address,uint256,uint256,uint256,uint256,uint256)"
)
RAY = 10**27  # Aave fixed-point scalar; rate / RAY == fractional APR

# Underlying reserve token -> display metadata. Keyed lowercase.
RESERVES: dict[str, dict] = {
    "0x5555555555555555555555555555555555555555": {"symbol": "wHYPE", "decimals": 18, "kind": "native"},
    "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": {"symbol": "USDe", "decimals": 18, "kind": "stable"},
    "0xb8ce59fc3717ada4c02eadf9682a9e934f625ebb": {"symbol": "USDT0", "decimals": 6, "kind": "stable"},
    "0xb88339cb7199b77e23db6e890353e22632ba630f": {"symbol": "USDC", "decimals": 6, "kind": "stable"},
    "0x111111a1a0667d36bd57c0a9f569b98057111111": {"symbol": "USDH", "decimals": 18, "kind": "stable"},
}

# Felix Protocol mints feUSD against HYPE collateral (a CDP, not an Aave pool),
# so it has no ReserveDataUpdated feed. We track feUSD as a stablecoin of
# interest; deeper Felix borrow-rate extraction would decode its own events
# via the GoldRush Pipeline API (see README).
FEUSD = "0x02c6a2fa58cc01a18b8d9e00ea48d65e4df26c70"

# --- HyperCore whale watchlist (use case 2) ---------------------------------
# Replace with the wallets you care about. The Info API batch endpoints accept
# up to 50 wallets per call with no rate limit, so a real deployment tracks
# thousands. These defaults are illustrative HyperCore accounts.
WHALE_WATCHLIST: list[str] = [
    "0xb0a55f13d22f66e6d495ac98113841b2326e9540",
    "0x31ca8395cf837de08b24da3f660e77761dfb974b",
    "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00",
    "0x73f9c53a8b15e43056d5599f6488ac9a8730f85d",
]

# The perp coin whose regime we score.
TARGET_COIN = "HYPE"

# --- Signal thresholds ------------------------------------------------------
@dataclass(frozen=True)
class Thresholds:
    # A flow is "large" once its absolute USD value crosses this.
    large_flow_usd: float = 100_000.0
    # Lookback for ledger flows, in hours.
    flow_lookback_hours: int = 24
    # A position sits in the "near liquidation" bucket when mark price is
    # within this fraction of its liquidation price.
    near_liq_pct: float = 0.10
    # Net-skew fraction past which whale positioning is called "crowded".
    crowded_skew: float = 0.60
    # Blocks of history to scan for lending ReserveDataUpdated events.
    lending_lookback_blocks: int = 50_000


@dataclass
class Settings:
    api_key: str = ""
    foundational_base_url: str = FOUNDATIONAL_BASE_URL
    info_base_url: str = INFO_BASE_URL
    chain_name: str = CHAIN_NAME
    whale_watchlist: list[str] = field(default_factory=lambda: list(WHALE_WATCHLIST))
    thresholds: Thresholds = field(default_factory=Thresholds)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(api_key=os.environ.get("GOLDRUSH_API_KEY", ""))
