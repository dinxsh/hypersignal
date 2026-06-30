// Mirrors the pydantic models returned by the hypersignal FastAPI backend.

export interface ReserveRate {
  symbol: string;
  reserve: string;
  kind: "native" | "stable" | "unknown";
  supply_apr_pct: number;
  borrow_apr_pct: number;
  block_height: number;
  updated_at: string | null;
}

export interface LendingSnapshot {
  market: string;
  pool: string;
  reserves: ReserveRate[];
}

export interface MarketContext {
  coin: string;
  mark_price: number;
  funding_rate: number;
  open_interest: number;
  day_volume: number;
}

export interface WhaleSnapshot {
  coin: string;
  market: MarketContext;
  wallets_scanned: number;
  wallets_with_position: number;
  total_account_value_usd: number;
  long_notional_usd: number;
  short_notional_usd: number;
  net_notional_usd: number;
  skew: number;
  crowded: boolean;
  near_liquidation: number;
  positioning: string;
}

export interface LargeFlow {
  wallet: string;
  direction: "in" | "out";
  type: string;
  usd: number;
  token: string;
  time_ms: number;
  hash: string | null;
}

export interface FlowSnapshot {
  window_hours: number;
  threshold_usd: number;
  wallets_scanned: number;
  inflow_usd: number;
  outflow_usd: number;
  net_flow_usd: number;
  large_event_count: number;
  direction: "accumulation" | "distribution" | "neutral";
  events: LargeFlow[];
}

export interface RegimeSignal {
  coin: string;
  directional_bias: number;
  volatility_score: number;
  regime: string;
  drivers: string[];
  hype_supply_apr: number | null;
  hype_borrow_apr: number | null;
  funding_rate: number;
  whale_skew: number;
  net_flow_usd: number;
}

export interface MarketRow {
  coin: string;
  mark_price: number;
  change_24h_pct: number;
  funding_rate: number;
  open_interest_usd: number;
  day_volume_usd: number;
}
export interface MarketsOverview {
  rows: MarketRow[];
}

export interface Candle {
  t: number;
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
}
export interface PriceSeries {
  coin: string;
  interval: string;
  candles: Candle[];
  last: number;
  change_pct: number;
  high: number;
  low: number;
}

export interface BookLevel {
  px: number;
  sz: number;
}
export interface OrderBook {
  coin: string;
  mid: number;
  spread: number;
  spread_bps: number;
  bids: BookLevel[];
  asks: BookLevel[];
  bid_depth: number;
  ask_depth: number;
}

export interface WhaleFill {
  coin: string;
  dir: string;
  side: string;
  px: number;
  sz: number;
  usd: number;
  closed_pnl: number;
  time_ms: number;
}
export interface WhaleTape {
  wallet: string;
  fills: WhaleFill[];
}

export interface MarketBundle {
  overview: MarketsOverview;
  price: PriceSeries;
  orderbook: OrderBook;
  tape: WhaleTape;
}

export interface HyperSignalReport {
  generated_at: string;
  mode: "live" | "offline";
  signal: RegimeSignal;
  lending: LendingSnapshot;
  whales: WhaleSnapshot;
  flows: FlowSnapshot;
  market: MarketBundle;
}
