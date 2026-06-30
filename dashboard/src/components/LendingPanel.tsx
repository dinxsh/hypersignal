import type { LendingSnapshot } from "../types";
import { pct } from "../format";
import { Panel } from "./Panel";

// Show the named reserves (HYPE + stablecoins) first — the ones Harmonix
// allocates against — then any other HyperLend markets.
const ORDER = ["wHYPE", "USDe", "USDT0", "USDC", "USDH"];

export function LendingPanel({ data }: { data: LendingSnapshot }) {
  const named = data.reserves.filter((r) => r.kind !== "unknown");
  const sorted = [...named].sort((a, b) => {
    const ia = ORDER.indexOf(a.symbol);
    const ib = ORDER.indexOf(b.symbol);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });
  const others = data.reserves.length - named.length;

  return (
    <Panel
      title="HyperEVM Lending"
      sub={`${data.market} · live supply / borrow APR`}
      endpoint="Foundational · events/address"
      delay={0.15}
    >
      <table className="tbl">
        <thead>
          <tr>
            <th>Asset</th>
            <th>Supply APR</th>
            <th>Borrow APR</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => {
            const isHype = r.symbol === "wHYPE";
            return (
              <tr key={r.reserve} className={isHype ? "row-hype" : ""}>
                <td>
                  <span className="asset">
                    <span className="sym">{isHype ? "HYPE" : r.symbol}</span>
                    <span className="badge">{r.kind}</span>
                  </span>
                </td>
                <td className="pos">{pct(r.supply_apr_pct)}</td>
                <td>{pct(r.borrow_apr_pct)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="note">
        Decoded from HyperLend's Aave-v3 <code>ReserveDataUpdated</code> events.
        {others > 0 ? ` +${others} other market${others > 1 ? "s" : ""} tracked.` : ""} feUSD borrow
        (Felix CDP) available via Pipeline API.
      </div>
    </Panel>
  );
}
