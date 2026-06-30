import { sinceNow } from "../format";

export function TopBar({
  mode,
  source,
  generatedAt,
  latencyMs,
  onRefresh,
  refreshing,
}: {
  mode: "live" | "offline";
  source: "live-backend" | "sample";
  generatedAt: string;
  latencyMs: number | null;
  onRefresh: () => void;
  refreshing: boolean;
}) {
  const isLive = source === "live-backend" && mode === "live";
  return (
    <header className="topbar">
      <div className="brand">
        <div className="mark">
          HARMONIX<span className="x">×</span><span className="gr">GOLDRUSH</span>
        </div>
        <div className="sub">HYPE Regime Cockpit</div>
      </div>
      <div className="topmeta">
        <span className={`chip ${isLive ? "live" : "sample"}`}>
          <span className="dot" />
          {isLive ? "LIVE · GoldRush" : "SAMPLE SNAPSHOT"}
        </span>
        <span className="chip">Info API · no rate limits</span>
        {latencyMs != null && <span className="chip">{latencyMs}ms</span>}
        <span className="chip">updated {sinceNow(generatedAt)}</span>
        <button className="refresh" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? "…" : "↻ refresh"}
        </button>
      </div>
    </header>
  );
}
