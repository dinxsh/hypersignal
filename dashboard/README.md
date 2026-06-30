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

Deploy from the **repo root** — the root [`vercel.json`](../vercel.json) builds this dashboard to static files. The deployed site renders the bundled real snapshot (`src/sample-report.json`); no key or backend needed.

```bash
vercel        # from repo root
```

For a hosted dashboard with **live** data, run the backend elsewhere and build against it:

```bash
VITE_API_URL=https://your-backend.example.com npm run build
```

See the root README's "Deploy to Vercel" for the full rationale.

## Data provenance

Each panel is labelled with the GoldRush endpoint behind it:

- **Lending** → Foundational API `events/address` (HyperLend `ReserveDataUpdated`)
- **Whales** → Info API `batchClearinghouseState` + `metaAndAssetCtxs`
- **Flows** → Info API `userNonFundingLedgerUpdates`
