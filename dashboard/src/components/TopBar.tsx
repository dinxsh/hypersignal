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
        <a
          className="chip chip-link"
          href="https://goldrush.dev/docs/goldrush-hyperliquid/info-api/limits"
          target="_blank"
          rel="noreferrer"
          title="GoldRush Hyperliquid Info API — rate limits & caching"
        >
          Info API · no rate limits ↗
        </a>
        {latencyMs != null && <span className="chip">{latencyMs}ms</span>}
        <span className="chip">updated {sinceNow(generatedAt)}</span>
        <button className="refresh" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? "…" : "↻ refresh"}
        </button>
      </div>
    </header>
  );
}
