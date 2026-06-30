"""Use case 2 -- HyperCore whale positioning for HYPE volatility outlook.

We read live market context (mark price, funding, open interest) via
``metaAndAssetCtxs`` and pull perp account state for a watchlist of large
wallets via ``batchClearinghouseState`` (up to 50 wallets per call, no rate
limit). Aggregating their HYPE exposure tells you whether the whales are
crowded long or short, how much is sitting near liquidation, and whether
funding is paying longs or shorts -- the ingredients of a volatility call.
"""
from __future__ import annotations

from pydantic import BaseModel

from .config import Settings, TARGET_COIN
from .goldrush import InfoClient


def _f(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


class MarketContext(BaseModel):
    coin: str
    mark_price: float
    funding_rate: float  # per-hour funding, signed (positive => longs pay shorts)
    open_interest: float
    day_volume: float


class WhaleSnapshot(BaseModel):
    coin: str
    market: MarketContext
    wallets_scanned: int
    wallets_with_position: int
    total_account_value_usd: float
    long_notional_usd: float
    short_notional_usd: float
    net_notional_usd: float
    skew: float  # net / gross, in [-1, 1]; +1 = all long
    crowded: bool
    near_liquidation: int  # positions within near_liq_pct of liquidation
    positioning: str  # human-readable label


def extract_market(meta_and_ctxs: list, coin: str) -> MarketContext:
    """Pull the live context for ``coin`` out of a metaAndAssetCtxs tuple."""
    meta, ctxs = meta_and_ctxs[0], meta_and_ctxs[1]
    universe = meta["universe"]
    idx = next((i for i, a in enumerate(universe) if a["name"] == coin), None)
    if idx is None or idx >= len(ctxs):
        return MarketContext(coin=coin, mark_price=0.0, funding_rate=0.0, open_interest=0.0, day_volume=0.0)
    ctx = ctxs[idx]
    return MarketContext(
        coin=coin,
        mark_price=_f(ctx.get("markPx")),
        funding_rate=_f(ctx.get("funding")),
        open_interest=_f(ctx.get("openInterest")),
        day_volume=_f(ctx.get("dayNtlVlm")),
    )


def parse_whales(
    meta_and_ctxs: list,
    states: list[dict],
    settings: Settings,
    coin: str = TARGET_COIN,
) -> WhaleSnapshot:
    market = extract_market(meta_and_ctxs, coin)
    th = settings.thresholds

    long_usd = short_usd = 0.0
    with_position = 0
    near_liq = 0
    total_av = 0.0

    for slot in states:
        if not isinstance(slot, dict) or slot.get("error"):
            continue  # upstream batch slot error -> skip this wallet
        total_av += _f(slot.get("marginSummary", {}).get("accountValue"))
        for ap in slot.get("assetPositions", []):
            pos = ap.get("position", {})
            if pos.get("coin") != coin:
                continue
            szi = _f(pos.get("szi"))
            if szi == 0:
                continue
            with_position += 1
            notional = abs(_f(pos.get("positionValue"))) or abs(szi) * market.mark_price
            if szi > 0:
                long_usd += notional
            else:
                short_usd += notional

            liq_px = _f(pos.get("liquidationPx"))
            if liq_px > 0 and market.mark_price > 0:
                if abs(market.mark_price - liq_px) / market.mark_price <= th.near_liq_pct:
                    near_liq += 1

    gross = long_usd + short_usd
    net = long_usd - short_usd
    skew = (net / gross) if gross > 0 else 0.0
    crowded = abs(skew) >= th.crowded_skew

    positioning = _label(skew, crowded, market.funding_rate)

    return WhaleSnapshot(
        coin=coin,
        market=market,
        wallets_scanned=len(states),
        wallets_with_position=with_position,
        total_account_value_usd=round(total_av, 2),
        long_notional_usd=round(long_usd, 2),
        short_notional_usd=round(short_usd, 2),
        net_notional_usd=round(net, 2),
        skew=round(skew, 4),
        crowded=crowded,
        near_liquidation=near_liq,
        positioning=positioning,
    )


def _label(skew: float, crowded: bool, funding: float) -> str:
    side = "long" if skew > 0 else "short" if skew < 0 else "balanced"
    if not crowded:
        return f"mildly {side}" if side != "balanced" else "balanced"
    # Crowded one way while funding pays the same way = squeeze fuel.
    if side == "long" and funding > 0:
        return "crowded long, longs paying funding (squeeze risk down)"
    if side == "short" and funding < 0:
        return "crowded short, shorts paying funding (squeeze risk up)"
    return f"crowded {side}"


def fetch_whales(client: InfoClient, settings: Settings, coin: str = TARGET_COIN) -> WhaleSnapshot:
    """Live fetch: market context + batched whale state for the watchlist."""
    meta_and_ctxs = client.meta_and_asset_ctxs()
    states: list[dict] = []
    wl = settings.whale_watchlist
    for i in range(0, len(wl), 50):  # 50 wallets per batch call
        states.extend(client.batch_clearinghouse_state(wl[i : i + 50]))
    return parse_whales(meta_and_ctxs, states, settings, coin)
