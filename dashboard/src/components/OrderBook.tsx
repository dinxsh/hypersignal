import type { OrderBook as Book } from "../types";
import { price } from "../format";
import { Panel } from "./Panel";

// HYPE L2 order book — depth bars + spread.
export function OrderBook({ data }: { data: Book }) {
  const rows = 7;
  const bids = data.bids.slice(0, rows);
  const asks = data.asks.slice(0, rows);
  const maxSz = Math.max(1, ...bids.map((b) => b.sz), ...asks.map((a) => a.sz));

  return (
    <Panel title={`${data.coin} Order Book`} sub="aggregated L2 depth" endpoint="Info · l2Book" delay={0.25}>
      <div className="ob">
        <div className="ob-side">
          {asks
            .slice()
            .reverse()
            .map((a, i) => (
              <div className="ob-row" key={`a${i}`}>
                <div className="ob-fill ask" style={{ width: `${(a.sz / maxSz) * 100}%` }} />
                <span className="ob-px neg">{price(a.px)}</span>
                <span className="ob-sz">{a.sz.toFixed(2)}</span>
              </div>
            ))}
        </div>
        <div className="ob-mid">
          <span className="ob-spread">spread {data.spread_bps.toFixed(2)} bps</span>
          <span className="ob-midpx">{price(data.mid)}</span>
        </div>
        <div className="ob-side">
          {bids.map((b, i) => (
            <div className="ob-row" key={`b${i}`}>
              <div className="ob-fill bid" style={{ width: `${(b.sz / maxSz) * 100}%` }} />
              <span className="ob-px pos">{price(b.px)}</span>
              <span className="ob-sz">{b.sz.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
}
