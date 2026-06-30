import type { WhaleSnapshot } from "../types";
import { usdCompact, price, fundingHourly } from "../format";
import { Panel } from "./Panel";

export function WhalesPanel({ data }: { data: WhaleSnapshot }) {
  const gross = data.long_notional_usd + data.short_notional_usd;
  const longPct = gross > 0 ? (data.long_notional_usd / gross) * 100 : 50;
  const shortPct = 100 - longPct;

  return (
    <Panel
      title="HyperCore Whales"
      sub={`${data.wallets_with_position}/${data.wallets_scanned} watched wallets hold ${data.coin}`}
      endpoint="Info · batchClearinghouseState"
      delay={0.25}
    >
      <div className="skew">
        <div className="skew-bar">
          <div className="short" style={{ width: `${shortPct}%` }} />
          <div className="long" style={{ width: `${longPct}%` }} />
          <div className="mid" />
        </div>
        <div className="skew-legend">
          <span className="neg">{usdCompact(data.short_notional_usd)} short</span>
          <span style={{ color: "var(--faint)" }}>skew {data.skew >= 0 ? "+" : ""}{data.skew.toFixed(2)}</span>
          <span className="pos">{usdCompact(data.long_notional_usd)} long</span>
        </div>
      </div>

      <div style={{ fontFamily: "var(--font-mono)", fontSize: 12.5, color: "var(--muted)", marginBottom: 16 }}>
        {data.positioning}
      </div>

      <div className="statgrid">
        <div className="cell">
          <div className="k">Mark price</div>
          <div className="v">{price(data.market.mark_price)}</div>
        </div>
        <div className="cell">
          <div className="k">Funding</div>
          <div className="v" style={{ color: data.market.funding_rate >= 0 ? "var(--mint)" : "var(--coral)" }}>
            {fundingHourly(data.market.funding_rate)}
          </div>
        </div>
        <div className="cell">
          <div className="k">Net exposure</div>
          <div className="v" style={{ color: data.net_notional_usd >= 0 ? "var(--mint)" : "var(--coral)" }}>
            {usdCompact(data.net_notional_usd)}
          </div>
        </div>
        <div className="cell">
          <div className="k">Near liquidation</div>
          <div className="v" style={{ color: data.near_liquidation ? "var(--amber)" : "var(--text)" }}>
            {data.near_liquidation}
          </div>
        </div>
        <div className="cell">
          <div className="k">Whale AUM tracked</div>
          <div className="v">{usdCompact(data.total_account_value_usd)}</div>
        </div>
        <div className="cell">
          <div className="k">Wallets w/ HYPE</div>
          <div className="v">
            {data.wallets_with_position}
            <span style={{ color: "var(--faint)" }}>/{data.wallets_scanned}</span>
          </div>
        </div>
      </div>
    </Panel>
  );
}
