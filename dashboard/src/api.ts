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

// Always prefer live GoldRush data. Retry a few times (serverless cold starts
// + the ~5s live fetch) before falling back to the bundled snapshot — the
// fallback is a last resort, not the goal.
const ATTEMPTS = 3;

export async function fetchReport(coin = "HYPE"): Promise<FetchResult> {
  const started = performance.now();
  for (let attempt = 0; attempt < ATTEMPTS; attempt++) {
    try {
      const res = await fetch(`${API_BASE}/report?coin=${coin}`, {
        signal: AbortSignal.timeout(25_000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const report = (await res.json()) as HyperSignalReport;
      return { report, source: "live-backend", latencyMs: Math.round(performance.now() - started) };
    } catch {
      if (attempt < ATTEMPTS - 1) {
        await new Promise((r) => setTimeout(r, 800 * (attempt + 1))); // backoff
      }
    }
  }
  return { report: sample as HyperSignalReport, source: "sample", latencyMs: null };
}
