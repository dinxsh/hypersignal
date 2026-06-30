import type { HyperSignalReport } from "./types";
import sample from "./sample-report.json";
import { fetchLiveReport, hasLiveKey } from "./live";

// API base resolution for the backend path (used when no in-browser key):
// - VITE_API_URL set            -> use it (separate API project)
// - dev                         -> "/api" (Vite proxy -> local FastAPI :8000)
// - production, no VITE_API_URL  -> "" same-origin (full-stack single project)
const API_BASE = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "/api" : "");

export type Source = "live-direct" | "live-backend" | "sample";

export interface FetchResult {
  report: HyperSignalReport;
  source: Source;
  latencyMs: number | null;
}

const ATTEMPTS = 3;

// Always prefer live GoldRush data:
// 1. If a browser key is set, call GoldRush directly (CORS is open) — no backend needed.
// 2. Otherwise hit the backend /report (retrying for serverless cold starts).
// 3. Only then fall back to the bundled snapshot.
export async function fetchReport(coin = "HYPE"): Promise<FetchResult> {
  const started = performance.now();

  if (hasLiveKey) {
    try {
      const report = await fetchLiveReport(coin);
      return { report, source: "live-direct", latencyMs: Math.round(performance.now() - started) };
    } catch {
      /* fall through to backend / sample */
    }
  }

  for (let attempt = 0; attempt < ATTEMPTS; attempt++) {
    try {
      const res = await fetch(`${API_BASE}/report?coin=${coin}`, { signal: AbortSignal.timeout(25_000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const report = (await res.json()) as HyperSignalReport;
      return { report, source: "live-backend", latencyMs: Math.round(performance.now() - started) };
    } catch {
      if (attempt < ATTEMPTS - 1) await new Promise((r) => setTimeout(r, 800 * (attempt + 1)));
    }
  }

  return { report: sample as HyperSignalReport, source: "sample", latencyMs: null };
}
