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

export interface HyperSignalReport {
  generated_at: string;
  mode: "live" | "offline";
  signal: RegimeSignal;
  lending: LendingSnapshot;
  whales: WhaleSnapshot;
  flows: FlowSnapshot;
}
