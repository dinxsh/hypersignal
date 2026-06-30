import type { MarketsOverview } from "../types";
import { price, usdCompact, signedPct, fundingHourly } from "../format";
import { Panel } from "./Panel";

// Top HyperCore perps by 24h volume — one metaAndAssetCtxs call, lots of data.
export function MarketsTable({ data, target }: { data: MarketsOverview; target: string }) {
  return (
    <Panel
      title="HyperCore Perps"
      sub="top markets by 24h volume"
      endpoint="Info · metaAndAssetCtxs"
      delay={0.2}
    >
      <table className="tbl mkt-tbl">
        <thead>
          <tr>
            <th>Coin</th>
            <th className="r">Mark</th>
            <th className="r">24h</th>
            <th className="r">Funding</th>
            <th className="r">OI</th>
            <th className="r">Vol 24h</th>
          </tr>
        </thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={r.coin} className={r.coin === target ? "row-hype" : ""}>
              <td>
                <span className="sym">{r.coin}</span>
              </td>
              <td className="r">{price(r.mark_price)}</td>
              <td className={`r ${r.change_24h_pct >= 0 ? "pos" : "neg"}`}>{signedPct(r.change_24h_pct)}</td>
              <td className={`r ${r.funding_rate >= 0 ? "pos" : "neg"}`}>{fundingHourly(r.funding_rate)}</td>
              <td className="r">{usdCompact(r.open_interest_usd)}</td>
              <td className="r">{usdCompact(r.day_volume_usd)}</td>
            </tr>
          ))}
          {data.rows.length === 0 && (
            <tr>
              <td colSpan={6} style={{ color: "var(--faint)", textAlign: "center", padding: "16px 0" }}>
                no market data
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </Panel>
  );
}
