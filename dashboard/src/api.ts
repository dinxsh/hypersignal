import type { HyperSignalReport } from "./types";
import sample from "./sample-report.json";

// API base resolution:
// - VITE_API_URL set            -> use it (two-project deploy: dashboard + API)
// - dev                         -> "/api" (Vite proxy -> local FastAPI :8000)
// - production, no VITE_API_URL  -> "" same-origin (single Vercel project where
//                                   FastAPI serves this built dashboard at / )
const API_BASE = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "/api" : "");

export interface FetchResult {
  report: HyperSignalReport;
  source: "live-backend" | "sample";
  latencyMs: number | null;
}

// Try the live backend; fall back to the bundled real snapshot so the
// dashboard always renders (e.g. `npm run dev` with no backend running).
export async function fetchReport(coin = "HYPE"): Promise<FetchResult> {
  const started = performance.now();
  try {
    const res = await fetch(`${API_BASE}/report?coin=${coin}`, {
      signal: AbortSignal.timeout(20_000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const report = (await res.json()) as HyperSignalReport;
    return { report, source: "live-backend", latencyMs: Math.round(performance.now() - started) };
  } catch {
    return { report: sample as HyperSignalReport, source: "sample", latencyMs: null };
  }
}
