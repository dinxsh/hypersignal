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

Deploy this folder as a **static Vite site** and set one env var. The dashboard calls GoldRush **directly from the browser** (open CORS), so there's no backend, no Python, no serverless — and it shows **live** data.

1. New Vercel project → import the repo → **Root Directory: `dashboard`** (auto-detected as Vite).
2. **Environment Variables** → add **`VITE_GOLDRUSH_API_KEY`** = your key → Deploy.

```bash
vercel                                   # Root Directory: dashboard
vercel env add VITE_GOLDRUSH_API_KEY     # then redeploy
```

Badge reads **LIVE · GoldRush**, refreshes every 30s.

> **Security:** this key ships in the built JS bundle (extractable) — use a rotatable / usage-capped key for public deploys. To keep the key server-side instead, leave `VITE_GOLDRUSH_API_KEY` unset and point `VITE_API_URL` at a hypersignal backend; the dashboard then falls back backend → snapshot.

## Data provenance

Each panel is labelled with the GoldRush endpoint behind it:

- **Lending** → Foundational API `events/address` (HyperLend `ReserveDataUpdated`)
- **Whales** → Info API `batchClearinghouseState` + `metaAndAssetCtxs`
- **Flows** → Info API `userNonFundingLedgerUpdates`
