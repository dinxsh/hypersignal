import type { FlowSnapshot } from "../types";
import { usdCompact, shortAddr } from "../format";
import { Panel } from "./Panel";

export function FlowsPanel({ data }: { data: FlowSnapshot }) {
  const gross = data.inflow_usd + data.outflow_usd;
  const inPct = gross > 0 ? (data.inflow_usd / gross) * 100 : 0;
  const net = data.net_flow_usd;

  return (
    <Panel
      title="HyperCore Flows"
      sub={`deposits / withdrawals · last ${data.window_hours}h · ≥ ${usdCompact(data.threshold_usd)}`}
      endpoint="Info · nonFundingLedgerUpdates"
      delay={0.35}
    >
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
        <div>
          <div className="bignum" style={{ color: net >= 0 ? "var(--mint)" : "var(--coral)" }}>
            {net >= 0 ? "+" : ""}
            {usdCompact(net)}
          </div>
          <div className="bignum-sub">net flow</div>
        </div>
        <span className={`dir-pill dir-${data.direction}`}>{data.direction}</span>
      </div>

      <div className="flowsplit">
        <div className="in" style={{ width: `${inPct}%` }} />
        <div className="out" style={{ width: `${100 - inPct}%` }} />
      </div>
      <div className="flow-note">
        <span className="pos">{usdCompact(data.inflow_usd)} in</span>
        <span className="neg">{usdCompact(data.outflow_usd)} out</span>
      </div>

      <table className="tbl flows-tbl" style={{ marginTop: 18 }}>
        <thead>
          <tr>
            <th>Wallet</th>
            <th className="c">Dir</th>
            <th className="r">Size</th>
          </tr>
        </thead>
        <tbody>
          {data.events.slice(0, 6).map((e, i) => (
            <tr key={`${e.hash}-${i}`}>
              <td>{shortAddr(e.wallet)}</td>
              <td className={`c ${e.direction === "in" ? "pos" : "neg"}`}>
                {e.direction === "in" ? "IN" : "OUT"}
              </td>
              <td className="r">{usdCompact(e.usd)}</td>
            </tr>
          ))}
          {data.events.length === 0 && (
            <tr>
              <td colSpan={3} style={{ color: "var(--faint)", textAlign: "center", padding: "16px 0" }}>
                no large flows in window
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </Panel>
  );
}
