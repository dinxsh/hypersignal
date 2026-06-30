"""Extra live market context from the GoldRush Hyperliquid Info API.

This is the "what else can GoldRush do" layer on top of the core signal:

* Markets overview  -> metaAndAssetCtxs  (top perps: price, 24h%, funding, OI, vol)
* Price candles     -> candleSnapshot    (HYPE OHLCV for the chart)
* Order book        -> l2Book            (HYPE depth + spread)
* Whale trade tape  -> userFills         (a watched wallet's recent fills)

Every parser is defensive: bad/missing data yields an empty result rather than
raising, so one slow endpoint never blanks the dashboard.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from .config import Settings, TARGET_COIN
from .goldrush import InfoClient


def _f(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------- markets table
class MarketRow(BaseModel):
    coin: str
    mark_price: float
    change_24h_pct: float
    funding_rate: float
    open_interest_usd: float
    day_volume_usd: float


class MarketsOverview(BaseModel):
    rows: list[MarketRow]


def parse_markets(meta_and_ctxs: list, top: int = 10, target: str = TARGET_COIN) -> MarketsOverview:
    try:
        meta, ctxs = meta_and_ctxs[0], meta_and_ctxs[1]
        universe = meta["universe"]
    except (KeyError, IndexError, TypeError):
        return MarketsOverview(rows=[])

    rows: list[MarketRow] = []
    for i, asset in enumerate(universe):
        if i >= len(ctxs):
            break
        c = ctxs[i]
        mark = _f(c.get("markPx"))
        prev = _f(c.get("prevDayPx"))
        change = ((mark - prev) / prev * 100) if prev else 0.0
        rows.append(
            MarketRow(
                coin=asset.get("name", "?"),
                mark_price=mark,
                change_24h_pct=round(change, 2),
                funding_rate=_f(c.get("funding")),
                open_interest_usd=round(_f(c.get("openInterest")) * mark, 0),
                day_volume_usd=round(_f(c.get("dayNtlVlm")), 0),
            )
        )

    rows.sort(key=lambda r: r.day_volume_usd, reverse=True)
    # Keep the top-by-volume, but always include the target coin.
    head = rows[:top]
    if target not in {r.coin for r in head}:
        tgt = next((r for r in rows if r.coin == target), None)
        if tgt:
            head = head[: top - 1] + [tgt]
    return MarketsOverview(rows=head)


# ----------------------------------------------------------------- price series
class Candle(BaseModel):
    t: int  # open time, ms
    o: float
    h: float
    l: float
    c: float
    v: float


class PriceSeries(BaseModel):
    coin: str
    interval: str
    candles: list[Candle]
    last: float
    change_pct: float  # over the window
    high: float
    low: float


def parse_candles(raw: list, coin: str, interval: str) -> PriceSeries:
    candles: list[Candle] = []
    for k in raw or []:
        try:
            candles.append(Candle(t=int(k["t"]), o=_f(k["o"]), h=_f(k["h"]), l=_f(k["l"]), c=_f(k["c"]), v=_f(k["v"])))
        except (KeyError, TypeError, ValueError):
            continue
    if not candles:
        return PriceSeries(coin=coin, interval=interval, candles=[], last=0, change_pct=0, high=0, low=0)
    last = candles[-1].c
    first_open = candles[0].o
    return PriceSeries(
        coin=coin,
        interval=interval,
        candles=candles,
        last=last,
        change_pct=round(((last - first_open) / first_open * 100) if first_open else 0.0, 2),
        high=max(c.h for c in candles),
        low=min(c.l for c in candles),
    )


# ------------------------------------------------------------------- order book
class BookLevel(BaseModel):
    px: float
    sz: float


class OrderBook(BaseModel):
    coin: str
    mid: float
    spread: float
    spread_bps: float
    bids: list[BookLevel]
    asks: list[BookLevel]
    bid_depth: float  # summed size of returned bid levels
    ask_depth: float


def parse_orderbook(raw: dict, coin: str, depth: int = 10) -> OrderBook:
    try:
        levels = raw["levels"]
        bids_raw, asks_raw = levels[0], levels[1]
    except (KeyError, IndexError, TypeError):
        return OrderBook(coin=coin, mid=0, spread=0, spread_bps=0, bids=[], asks=[], bid_depth=0, ask_depth=0)

    bids = [BookLevel(px=_f(l["px"]), sz=_f(l["sz"])) for l in bids_raw[:depth]]
    asks = [BookLevel(px=_f(l["px"]), sz=_f(l["sz"])) for l in asks_raw[:depth]]
    best_bid = bids[0].px if bids else 0.0
    best_ask = asks[0].px if asks else 0.0
    mid = (best_bid + best_ask) / 2 if best_bid and best_ask else (best_bid or best_ask)
    spread = (best_ask - best_bid) if (best_bid and best_ask) else 0.0
    return OrderBook(
        coin=coin,
        mid=round(mid, 5),
        spread=round(spread, 5),
        spread_bps=round((spread / mid * 10_000) if mid else 0.0, 2),
        bids=bids,
        asks=asks,
        bid_depth=round(sum(b.sz for b in bids), 2),
        ask_depth=round(sum(a.sz for a in asks), 2),
    )


# -------------------------------------------------------------------- whale tape
class WhaleFill(BaseModel):
    coin: str
    dir: str
    side: str  # "B" | "A"
    px: float
    sz: float
    usd: float
    closed_pnl: float
    time_ms: int


class WhaleTape(BaseModel):
    wallet: str
    fills: list[WhaleFill]


def parse_fills(raw: list, wallet: str, limit: int = 12) -> WhaleTape:
    ordered = sorted(raw or [], key=lambda f: int(f.get("time", 0)), reverse=True)
    fills: list[WhaleFill] = []
    for fdata in ordered[:limit]:
        try:
            px = _f(fdata["px"])
            sz = _f(fdata["sz"])
            fills.append(
                WhaleFill(
                    coin=fdata.get("coin", "?"),
                    dir=fdata.get("dir", ""),
                    side=fdata.get("side", ""),
                    px=px,
                    sz=sz,
                    usd=round(px * sz, 2),
                    closed_pnl=_f(fdata.get("closedPnl")),
                    time_ms=int(fdata.get("time", 0)),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return WhaleTape(wallet=wallet, fills=fills)


# ----------------------------------------------------------------------- bundle
class MarketBundle(BaseModel):
    overview: MarketsOverview
    price: PriceSeries
    orderbook: OrderBook
    tape: WhaleTape


def fetch_market(client: InfoClient, settings: Settings, coin: str = TARGET_COIN) -> MarketBundle:
    """Live fetch of the extra market context.

    The four calls run concurrently (the userFills payload is large and slow),
    and each piece degrades to empty on error so the bundle always returns.
    """
    now = int(time.time() * 1000)
    start = now - 3 * 24 * 3600 * 1000  # 3 days of 1h candles
    wallet = settings.whale_watchlist[0] if settings.whale_watchlist else ""

    def g_overview() -> MarketsOverview:
        try:
            return parse_markets(client.meta_and_asset_ctxs(), top=10, target=coin)
        except Exception:
            return MarketsOverview(rows=[])

    def g_price() -> PriceSeries:
        try:
            return parse_candles(client.candle_snapshot(coin, "1h", start, now), coin, "1h")
        except Exception:
            return parse_candles([], coin, "1h")

    def g_book() -> OrderBook:
        try:
            return parse_orderbook(client.l2_book(coin), coin)
        except Exception:
            return parse_orderbook({}, coin)

    def g_tape() -> WhaleTape:
        try:
            return parse_fills(client.user_fills(wallet), wallet)
        except Exception:
            return parse_fills([], wallet)

    with ThreadPoolExecutor(max_workers=4) as ex:
        fo, fp, fb, ft = ex.submit(g_overview), ex.submit(g_price), ex.submit(g_book), ex.submit(g_tape)
        return MarketBundle(overview=fo.result(), price=fp.result(), orderbook=fb.result(), tape=ft.result())
