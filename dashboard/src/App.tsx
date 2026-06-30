import { useCallback, useEffect, useState } from "react";
import { fetchReport, type FetchResult } from "./api";
import { TopBar } from "./components/TopBar";
import { RegimeHero } from "./components/RegimeHero";
import { PriceChart } from "./components/PriceChart";
import { OrderBook } from "./components/OrderBook";
import { LendingPanel } from "./components/LendingPanel";
import { WhalesPanel } from "./components/WhalesPanel";
import { FlowsPanel } from "./components/FlowsPanel";
import { MarketsTable } from "./components/MarketsTable";
import { WhaleTape } from "./components/WhaleTape";

const REFRESH_MS = 30_000;

export default function App() {
  const [res, setRes] = useState<FetchResult | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setRefreshing(true);
    const r = await fetchReport("HYPE");
    setRes(r);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, [load]);

  if (!res) {
    return (
      <div className="loading">
        <div className="ring" />
        <div>READING HYPERLIQUID STATE…</div>
      </div>
    );
  }

  const { report } = res;
  return (
    <div className="shell">
      <TopBar
        mode={report.mode}
        source={res.source}
        generatedAt={report.generated_at}
        latencyMs={res.latencyMs}
        onRefresh={load}
        refreshing={refreshing}
      />

      <RegimeHero signal={report.signal} markPrice={report.whales.market.mark_price} />

      <div className="grid-2a">
        <PriceChart data={report.market.price} />
        <OrderBook data={report.market.orderbook} />
      </div>

      <div className="grid3">
        <LendingPanel data={report.lending} />
        <WhalesPanel data={report.whales} />
        <FlowsPanel data={report.flows} />
      </div>

      <div className="grid-2b">
        <MarketsTable data={report.market.overview} target={report.signal.coin} />
        <WhaleTape data={report.market.tape} />
      </div>

      <footer className="foot">
        <div className="stack">
          <span>Powered by</span>
          <a href="https://goldrush.dev/docs/goldrush-hyperliquid/overview" target="_blank" rel="noreferrer">
            GoldRush
          </a>
          <span>· Foundational API (HyperEVM) · Info API (HyperCore, rate-limit-free) · Pipeline API at scale</span>
        </div>
        <div>
          {res.source === "sample"
            ? "showing bundled live snapshot — start the backend for real-time"
            : `${report.mode} · HyperEVM chain 999`}
        </div>
      </footer>
    </div>
  );
}
