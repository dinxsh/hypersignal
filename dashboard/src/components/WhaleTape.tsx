import type { WhaleTape as Tape } from "../types";
import { usdCompact, shortAddr, clockTime } from "../format";
import { Panel } from "./Panel";

// A watched whale's most recent fills — live trade tape.
export function WhaleTape({ data }: { data: Tape }) {
  return (
    <Panel
      title="Whale Trade Tape"
      sub={data.wallet ? `recent fills · ${shortAddr(data.wallet)}` : "recent fills"}
      endpoint="Info · userFills"
      delay={0.3}
    >
      <table className="tbl tape-tbl">
        <thead>
          <tr>
            <th>Time</th>
            <th>Coin</th>
            <th>Side</th>
            <th className="r">Size</th>
            <th className="r">PnL</th>
          </tr>
        </thead>
        <tbody>
          {data.fills.map((f, i) => {
            const buy = f.side === "B";
            return (
              <tr key={`${f.time_ms}-${i}`}>
                <td style={{ color: "var(--faint)" }}>{clockTime(f.time_ms)}</td>
                <td>
                  <span className="sym">{f.coin}</span>
                </td>
                <td className={buy ? "pos" : "neg"}>{f.dir || (buy ? "Buy" : "Sell")}</td>
                <td className="r">{usdCompact(f.usd)}</td>
                <td className={`r ${f.closed_pnl > 0 ? "pos" : f.closed_pnl < 0 ? "neg" : ""}`}>
                  {f.closed_pnl ? usdCompact(f.closed_pnl) : "—"}
                </td>
              </tr>
            );
          })}
          {data.fills.length === 0 && (
            <tr>
              <td colSpan={5} style={{ color: "var(--faint)", textAlign: "center", padding: "16px 0" }}>
                no recent fills
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </Panel>
  );
}
