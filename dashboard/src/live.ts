// Browser-direct GoldRush client: computes a full live HyperSignalReport in the
// browser. GoldRush's Info + Foundational APIs send permissive CORS headers, so
// the dashboard needs no backend — a pure static deploy goes live as long as
// VITE_GOLDRUSH_API_KEY is set at build time. (TS port of the Python engine.)
import type {
  HyperSignalReport,
  LendingSnapshot,
  ReserveRate,
  WhaleSnapshot,
  FlowSnapshot,
  LargeFlow,
  MarketBundle,
  MarketRow,
  Candle,
  PriceSeries,
  OrderBook,
  BookLevel,
  WhaleFill,
  RegimeSignal,
} from "./types";

export const GOLDRUSH_KEY: string = import.meta.env.VITE_GOLDRUSH_API_KEY ?? "";
export const hasLiveKey = GOLDRUSH_KEY.length > 0;

const FOUNDATIONAL = "https://api.covalenthq.com/v1";
const INFO = "https://hypercore.goldrushdata.com";
const CHAIN = "hyperevm-mainnet";
const POOL = "0x00A89d7a5A02160f20150EbEA7a2b5E4879A1A8b";
const RDU_TOPIC = "0x804c9b842b2748a22bb64b345453a3de7ca54a6ca45ce00d415894979e22897a";
const RAY = 1e27;
const LOOKBACK_BLOCKS = 50_000;
const LARGE_FLOW_USD = 100_000;
const FLOW_HOURS = 24;
const NEAR_LIQ_PCT = 0.1;
const CROWDED_SKEW = 0.6;

const RESERVES: Record<string, { symbol: string; kind: string }> = {
  "0x5555555555555555555555555555555555555555": { symbol: "wHYPE", kind: "native" },
  "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": { symbol: "USDe", kind: "stable" },
  "0xb8ce59fc3717ada4c02eadf9682a9e934f625ebb": { symbol: "USDT0", kind: "stable" },
  "0xb88339cb7199b77e23db6e890353e22632ba630f": { symbol: "USDC", kind: "stable" },
  "0x111111a1a0667d36bd57c0a9f569b98057111111": { symbol: "USDH", kind: "stable" },
};

const WATCHLIST = [
  "0xb0a55f13d22f66e6d495ac98113841b2326e9540",
  "0x31ca8395cf837de08b24da3f660e77761dfb974b",
  "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00",
  "0x73f9c53a8b15e43056d5599f6488ac9a8730f85d",
];

const f = (v: unknown, d = 0): number => {
  const n = typeof v === "string" ? parseFloat(v) : (v as number);
  return Number.isFinite(n) ? n : d;
};
const clamp = (x: number, lo = -1, hi = 1) => Math.max(lo, Math.min(hi, x));
const round = (x: number, d = 2) => {
  const p = 10 ** d;
  return Math.round(x * p) / p;
};

async function info<T>(body: unknown): Promise<T> {
  const r = await fetch(`${INFO}/info`, {
    method: "POST",
    headers: { Authorization: `Bearer ${GOLDRUSH_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`info ${r.status}`);
  return r.json() as Promise<T>;
}

async function found(path: string, params: Record<string, string | number> = {}): Promise<any> {
  const qs = new URLSearchParams({ key: GOLDRUSH_KEY, ...Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)])) });
  const r = await fetch(`${FOUNDATIONAL}${path}?${qs}`);
  if (!r.ok) throw new Error(`found ${r.status}`);
  const j = await r.json();
  if (j?.error) throw new Error(j.error_message || "foundational error");
  return j.data ?? j;
}

// ---------------------------------------------------------------- lending
function word(dataHex: string, i: number): bigint {
  const raw = dataHex.startsWith("0x") ? dataHex.slice(2) : dataHex;
  const s = raw.slice(i * 64, i * 64 + 64) || "0";
  return BigInt("0x" + s);
}

async function fetchLending(): Promise<LendingSnapshot> {
  let items: any[] = [];
  try {
    const latestData = await found(`/${CHAIN}/block_v2/latest/`);
    const latest = Number(latestData?.items?.[0]?.height ?? 0);
    const data = await found(`/${CHAIN}/events/address/${POOL}/`, {
      "starting-block": Math.max(0, latest - LOOKBACK_BLOCKS),
      "page-size": 1000,
    });
    items = data?.items ?? [];
  } catch {
    items = [];
  }

  const latestByReserve: Record<string, ReserveRate> = {};
  for (const ev of items.sort((a, b) => (a.block_height ?? 0) - (b.block_height ?? 0))) {
    let reserve = "";
    let liq = 0n;
    let borrow = 0n;
    try {
      const decoded = ev.decoded;
      if (decoded && decoded.name === "ReserveDataUpdated") {
        const by: Record<string, string> = {};
        for (const p of decoded.params) by[p.name] = p.value;
        reserve = by["reserve"];
        liq = BigInt(by["liquidityRate"]);
        borrow = BigInt(by["variableBorrowRate"]);
      } else if (ev.raw_log_topics?.[0] === RDU_TOPIC) {
        reserve = "0x" + ev.raw_log_topics[1].slice(-40);
        liq = word(ev.raw_log_data, 0);
        borrow = word(ev.raw_log_data, 2);
      } else continue;
    } catch {
      continue;
    }
    const meta = RESERVES[reserve.toLowerCase()] ?? { symbol: reserve.slice(0, 10), kind: "unknown" };
    latestByReserve[reserve.toLowerCase()] = {
      symbol: meta.symbol,
      reserve,
      kind: meta.kind as ReserveRate["kind"],
      supply_apr_pct: round((Number(liq) / RAY) * 100, 4),
      borrow_apr_pct: round((Number(borrow) / RAY) * 100, 4),
      block_height: ev.block_height ?? 0,
      updated_at: ev.block_signed_at ?? null,
    };
  }
  const reserves = Object.values(latestByReserve).sort((a, b) => a.symbol.localeCompare(b.symbol));
  return { market: "HyperLend", pool: POOL, reserves };
}

// ---------------------------------------------------------------- whales
function whaleLabel(skew: number, crowded: boolean, funding: number): string {
  const side = skew > 0 ? "long" : skew < 0 ? "short" : "balanced";
  if (!crowded) return side === "balanced" ? "balanced" : `mildly ${side}`;
  if (side === "long" && funding > 0) return "crowded long, longs paying funding (squeeze risk down)";
  if (side === "short" && funding < 0) return "crowded short, shorts paying funding (squeeze risk up)";
  return `crowded ${side}`;
}

function marketCtx(meta: any, coin: string) {
  try {
    const uni = meta[0].universe;
    const idx = uni.findIndex((a: any) => a.name === coin);
    const c = meta[1][idx];
    return {
      coin,
      mark_price: f(c.markPx),
      funding_rate: f(c.funding),
      open_interest: f(c.openInterest),
      day_volume: f(c.dayNtlVlm),
    };
  } catch {
    return { coin, mark_price: 0, funding_rate: 0, open_interest: 0, day_volume: 0 };
  }
}

async function fetchWhales(meta: any, coin: string): Promise<WhaleSnapshot> {
  const market = marketCtx(meta, coin);
  let states: any[] = [];
  try {
    states = await info<any[]>({ type: "batchClearinghouseState", users: WATCHLIST });
  } catch {
    states = [];
  }
  let longUsd = 0;
  let shortUsd = 0;
  let withPos = 0;
  let nearLiq = 0;
  let totalAv = 0;
  for (const slot of states) {
    if (!slot || slot.error) continue;
    totalAv += f(slot.marginSummary?.accountValue);
    for (const ap of slot.assetPositions ?? []) {
      const pos = ap.position ?? {};
      if (pos.coin !== coin) continue;
      const szi = f(pos.szi);
      if (szi === 0) continue;
      withPos++;
      const notional = Math.abs(f(pos.positionValue)) || Math.abs(szi) * market.mark_price;
      if (szi > 0) longUsd += notional;
      else shortUsd += notional;
      const liqPx = f(pos.liquidationPx);
      if (liqPx > 0 && market.mark_price > 0 && Math.abs(market.mark_price - liqPx) / market.mark_price <= NEAR_LIQ_PCT) nearLiq++;
    }
  }
  const gross = longUsd + shortUsd;
  const net = longUsd - shortUsd;
  const skew = gross > 0 ? net / gross : 0;
  const crowded = Math.abs(skew) >= CROWDED_SKEW;
  return {
    coin,
    market,
    wallets_scanned: states.length,
    wallets_with_position: withPos,
    total_account_value_usd: round(totalAv),
    long_notional_usd: round(longUsd),
    short_notional_usd: round(shortUsd),
    net_notional_usd: round(net),
    skew: round(skew, 4),
    crowded,
    near_liquidation: nearLiq,
    positioning: whaleLabel(skew, crowded, market.funding_rate),
  };
}

// ---------------------------------------------------------------- flows
async function fetchFlows(): Promise<FlowSnapshot> {
  const startMs = Date.now() - FLOW_HOURS * 3600 * 1000;
  const perWallet = await Promise.all(
    WATCHLIST.map(async (w) => {
      try {
        return [w, await info<any[]>({ type: "userNonFundingLedgerUpdates", user: w, startTime: startMs })] as const;
      } catch {
        return [w, []] as const;
      }
    })
  );
  let inflow = 0;
  let outflow = 0;
  const events: LargeFlow[] = [];
  for (const [wallet, updates] of perWallet) {
    for (const upd of updates) {
      const delta = upd.delta ?? {};
      const dtype = String(delta.type ?? "").toLowerCase();
      const usd = f(delta.usdc ?? delta.usdcValue ?? delta.usdValue);
      if (usd < LARGE_FLOW_USD) continue;
      let direction: "in" | "out";
      if (dtype === "deposit") {
        inflow += usd;
        direction = "in";
      } else if (dtype === "withdraw") {
        outflow += usd;
        direction = "out";
      } else continue;
      events.push({ wallet, direction, type: dtype, usd: round(usd), token: String(delta.token ?? "USDC"), time_ms: Number(upd.time ?? 0), hash: upd.hash ?? null });
    }
  }
  const net = inflow - outflow;
  const dir = net > LARGE_FLOW_USD ? "accumulation" : net < -LARGE_FLOW_USD ? "distribution" : "neutral";
  events.sort((a, b) => b.usd - a.usd);
  return {
    window_hours: FLOW_HOURS,
    threshold_usd: LARGE_FLOW_USD,
    wallets_scanned: WATCHLIST.length,
    inflow_usd: round(inflow),
    outflow_usd: round(outflow),
    net_flow_usd: round(net),
    large_event_count: events.length,
    direction: dir,
    events,
  };
}

// ---------------------------------------------------------------- market
function parseMarkets(meta: any, top: number, target: string): MarketRow[] {
  try {
    const uni = meta[0].universe;
    const ctxs = meta[1];
    const rows: MarketRow[] = uni.slice(0, ctxs.length).map((a: any, i: number) => {
      const c = ctxs[i];
      const mark = f(c.markPx);
      const prev = f(c.prevDayPx);
      return {
        coin: a.name,
        mark_price: mark,
        change_24h_pct: round(prev ? ((mark - prev) / prev) * 100 : 0),
        funding_rate: f(c.funding),
        open_interest_usd: round(f(c.openInterest) * mark, 0),
        day_volume_usd: round(f(c.dayNtlVlm), 0),
      };
    });
    rows.sort((a, b) => b.day_volume_usd - a.day_volume_usd);
    const head = rows.slice(0, top);
    if (!head.some((r) => r.coin === target)) {
      const tgt = rows.find((r) => r.coin === target);
      if (tgt) head[head.length - 1] = tgt;
    }
    return head;
  } catch {
    return [];
  }
}

async function fetchMarket(meta: any, coin: string): Promise<MarketBundle> {
  const now = Date.now();
  const start = now - 3 * 24 * 3600 * 1000;
  const [candlesRaw, bookRaw, fillsRaw] = await Promise.all([
    info<any[]>({ type: "candleSnapshot", req: { coin, interval: "1h", startTime: start, endTime: now } }).catch(() => []),
    info<any>({ type: "l2Book", coin }).catch(() => ({})),
    info<any[]>({ type: "userFills", user: WATCHLIST[0] }).catch(() => []),
  ]);

  const candles: Candle[] = (candlesRaw ?? []).map((k: any) => ({ t: Number(k.t), o: f(k.o), h: f(k.h), l: f(k.l), c: f(k.c), v: f(k.v) }));
  const price: PriceSeries = candles.length
    ? {
        coin,
        interval: "1h",
        candles,
        last: candles[candles.length - 1].c,
        change_pct: round(((candles[candles.length - 1].c - candles[0].o) / candles[0].o) * 100),
        high: Math.max(...candles.map((c) => c.h)),
        low: Math.min(...candles.map((c) => c.l)),
      }
    : { coin, interval: "1h", candles: [], last: 0, change_pct: 0, high: 0, low: 0 };

  const lv = bookRaw?.levels ?? [[], []];
  const bids: BookLevel[] = (lv[0] ?? []).slice(0, 10).map((l: any) => ({ px: f(l.px), sz: f(l.sz) }));
  const asks: BookLevel[] = (lv[1] ?? []).slice(0, 10).map((l: any) => ({ px: f(l.px), sz: f(l.sz) }));
  const bestBid = bids[0]?.px ?? 0;
  const bestAsk = asks[0]?.px ?? 0;
  const mid = bestBid && bestAsk ? (bestBid + bestAsk) / 2 : bestBid || bestAsk;
  const spread = bestBid && bestAsk ? bestAsk - bestBid : 0;
  const orderbook: OrderBook = {
    coin,
    mid: round(mid, 5),
    spread: round(spread, 5),
    spread_bps: round(mid ? (spread / mid) * 10000 : 0),
    bids,
    asks,
    bid_depth: round(bids.reduce((s, b) => s + b.sz, 0)),
    ask_depth: round(asks.reduce((s, a) => s + a.sz, 0)),
  };

  const fills: WhaleFill[] = (fillsRaw ?? [])
    .slice()
    .sort((a: any, b: any) => Number(b.time ?? 0) - Number(a.time ?? 0))
    .slice(0, 12)
    .map((x: any) => {
      const px = f(x.px);
      const sz = f(x.sz);
      return { coin: x.coin ?? "?", dir: x.dir ?? "", side: x.side ?? "", px, sz, usd: round(px * sz), closed_pnl: f(x.closedPnl), time_ms: Number(x.time ?? 0) };
    });

  return {
    overview: { rows: parseMarkets(meta, 10, coin) },
    price,
    orderbook,
    tape: { wallet: WATCHLIST[0], fills },
  };
}

// ---------------------------------------------------------------- signal
function regimeLabel(directional: number, volatility: number): string {
  const vol = volatility >= 0.6 ? "turbulent" : volatility >= 0.35 ? "choppy" : "calm";
  const bias = directional >= 0.25 ? "risk-on" : directional <= -0.25 ? "risk-off" : "neutral";
  return `${bias} / ${vol}`;
}

function buildSignal(lending: LendingSnapshot, whales: WhaleSnapshot, flows: FlowSnapshot, coin: string): RegimeSignal {
  const hype = lending.reserves.find((r) => r.symbol.toLowerCase() === "whype") ?? lending.reserves.find((r) => r.symbol.toLowerCase() === "hype");
  const hypeBorrow = hype?.borrow_apr_pct ?? 0;
  const hypeSupply = hype?.supply_apr_pct ?? 0;

  const flowComponent = clamp(flows.net_flow_usd / 2_000_000);
  const directional = clamp(0.6 * flowComponent + 0.4 * whales.skew);

  const drivers: string[] = [];
  if (flows.direction === "accumulation") drivers.push(`net $${Math.round(flows.net_flow_usd).toLocaleString()} deposited into HyperCore (accumulation)`);
  else if (flows.direction === "distribution") drivers.push(`net $${Math.round(-flows.net_flow_usd).toLocaleString()} withdrawn from HyperCore (distribution)`);
  drivers.push(`whale positioning ${whales.positioning} (skew ${whales.skew >= 0 ? "+" : ""}${whales.skew.toFixed(2)})`);

  const crowd = whales.crowded ? Math.abs(whales.skew) : Math.abs(whales.skew) * 0.5;
  const nearLiqRatio = whales.near_liquidation / Math.max(whales.wallets_with_position, 1);
  const borrowPressure = Math.min(hypeBorrow / 20, 1);
  const flowMag = Math.min(Math.abs(flows.net_flow_usd) / 2_000_000, 1);
  const volatility = round(Math.max(0, Math.min(1, 0.35 * crowd + 0.3 * nearLiqRatio + 0.2 * borrowPressure + 0.15 * flowMag)), 3);

  if (whales.near_liquidation) drivers.push(`${whales.near_liquidation} whale position(s) within ${Math.round(NEAR_LIQ_PCT * 100)}% of liquidation`);
  if (hypeBorrow) drivers.push(`HYPE lending: ${hypeSupply.toFixed(2)}% supply / ${hypeBorrow.toFixed(2)}% borrow APR`);
  if (whales.market.funding_rate) drivers.push(`funding ${whales.market.funding_rate >= 0 ? "+" : ""}${(whales.market.funding_rate * 100).toFixed(4)}%/hr`);

  return {
    coin,
    directional_bias: round(directional, 3),
    volatility_score: volatility,
    regime: regimeLabel(directional, volatility),
    drivers,
    hype_supply_apr: hypeSupply || null,
    hype_borrow_apr: hypeBorrow || null,
    funding_rate: whales.market.funding_rate,
    whale_skew: whales.skew,
    net_flow_usd: flows.net_flow_usd,
  };
}

// ---------------------------------------------------------------- orchestrate
export async function fetchLiveReport(coin = "HYPE"): Promise<HyperSignalReport> {
  const meta = await info<any>({ type: "metaAndAssetCtxs", dex: "" }).catch(() => [{ universe: [] }, []]);
  const [lending, whales, flows, market] = await Promise.all([fetchLending(), fetchWhales(meta, coin), fetchFlows(), fetchMarket(meta, coin)]);
  const signal = buildSignal(lending, whales, flows, coin);
  return {
    generated_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    mode: "live",
    signal,
    lending,
    whales,
    flows,
    market,
  };
}
