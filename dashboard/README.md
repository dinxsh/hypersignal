# HYPE Regime Cockpit — dashboard

A custom Vite + React dashboard over the `hypersignal` engine, built for **Harmonix**: one screen that turns HyperEVM lending rates, HyperCore whale positioning, and large flows into the **agent directive** their vault allocator acts on.

Dark "quant terminal" aesthetic — Hyperliquid mint on near-black, SVG bias gauge, live regime verdict.

## Run it

**Standalone (uses a bundled real snapshot — no key, no backend):**

```bash
cd dashboard
npm install
npm run dev          # http://localhost:5173
```

**Live (real-time, key stays server-side):**

```bash
# terminal 1 — start the hypersignal API with your key
cd ..
GOLDRUSH_API_KEY=cqt_... hypersignal serve     # http://127.0.0.1:8000

# terminal 2 — the dashboard proxies /api -> :8000
cd dashboard
npm run dev
```

The dashboard tries the backend first and falls back to the bundled snapshot if it isn't running, so it always renders. The GoldRush API key never reaches the browser — the FastAPI backend holds it and the Vite dev server proxies `/api`.

## Build

```bash
npm run build && npm run preview
```

## Deploy (Vercel)

This dashboard is **one of two Vercel projects** (the other is the FastAPI API). Create a Vercel project for this folder with **Root Directory: `dashboard`** — Vercel auto-detects Vite. Set env var **`VITE_API_URL`** to the API project's URL for live data; without it the dashboard renders the bundled snapshot (`src/sample-report.json`).

```bash
vercel          # Root Directory: dashboard
# set VITE_API_URL = https://<your-api-project>.vercel.app
```

Full two-project walkthrough: see the root README's "Deploy everything to Vercel".

## Data provenance

Each panel is labelled with the GoldRush endpoint behind it:

- **Lending** → Foundational API `events/address` (HyperLend `ReserveDataUpdated`)
- **Whales** → Info API `batchClearinghouseState` + `metaAndAssetCtxs`
- **Flows** → Info API `userNonFundingLedgerUpdates`
