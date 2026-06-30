# hypersignal

**A GoldRush-powered Hyperliquid signal engine for AI yield agents.**

`hypersignal` turns three on-chain data feeds — HyperEVM lending rates, HyperCore whale positioning, and large stablecoin/HYPE flows — into a single, explainable **HYPE regime signal** that an allocation agent can act on directly.

It is built entirely on the [GoldRush](https://goldrush.dev/docs) APIs, so it scales past the public Hyperliquid rate limits: the [Info API](https://goldrush.dev/docs/goldrush-hyperliquid/info-api/overview) is a drop-in, **rate-limit-free** replacement for `api.hyperliquid.xyz/info`, and the [Foundational API](https://goldrush.dev/docs/chains/hyperevm) indexes HyperEVM directly.

![HYPE Regime Cockpit — the dashboard rendering live GoldRush data](dashboard/preview.png)

> The screenshot above is **live** data: the bias gauge, lending APRs, whale skew, and HyperCore flows are all pulled through GoldRush in real time. See [`dashboard/`](dashboard/).

---

## Why this exists

This demo was scoped for a team running an AI agent that allocates across Hyperliquid lending markets (Felix, HyperLend) off a small set of cron-pulled data points. The three things they wanted to track:

1. **On-chain HyperEVM lending rates** for HYPE and stablecoins.
2. **Whale positioning on HyperCore** — a read on whether HYPE is set up to be volatile.
3. **Large deposits/withdrawals** of stablecoin/HYPE in and out of HyperEVM/HyperCore.

`hypersignal` does all three and fuses them, so the agent consumes one JSON object instead of stitching together raw feeds.

## How each use case maps to GoldRush

| Use case | Module | GoldRush endpoint | What it produces |
|---|---|---|---|
| **1. Lending rates** | [`lending.py`](src/hypersignal/lending.py) | Foundational API `GET /v1/hyperevm-mainnet/events/address/{pool}/` | Decodes HyperLend's Aave-v3 `ReserveDataUpdated` events into live **supply / borrow APR** per reserve (HYPE, USDe, USDT0, USDC, USDH) |
| **2. Whale positioning** | [`whales.py`](src/hypersignal/whales.py) | Info API `metaAndAssetCtxs` + `batchClearinghouseState` | Net whale HYPE exposure, **skew**, crowding, liquidation clustering, funding |
| **3. Large flows** | [`flows.py`](src/hypersignal/flows.py) | Info API `userNonFundingLedgerUpdates` | Large deposits/withdrawals over a window → **net flow direction** (accumulation vs distribution) |
| **Fusion** | [`signal.py`](src/hypersignal/signal.py) | — | `directional_bias ∈ [-1,1]`, `volatility_score ∈ [0,1]`, regime label, plain-English drivers |

> **On rates, precisely:** HyperLend is an Aave v3.0.2 friendly-fork. Its Pool emits `ReserveDataUpdated(reserve, liquidityRate, …, variableBorrowRate, …)` on every interaction, with rates in RAY (1e27). `hypersignal` reads those events through GoldRush and computes `APR% = rate / 1e27 × 100` — the *exact* on-chain rate, market-wide, in one request. Felix mints feUSD against HYPE collateral (a CDP, not an Aave pool), so it has no rate feed; feUSD is tracked as a stablecoin of interest.

## Quickstart

```bash
git clone https://github.com/dinxsh/hypersignal
cd hypersignal
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run against recorded fixtures — no API key needed:
hypersignal signal --offline
```

Example output:

```json
{
  "coin": "HYPE",
  "directional_bias": 0.876,
  "volatility_score": 0.571,
  "regime": "risk-on / choppy",
  "drivers": [
    "net $1,900,000 deposited into HyperCore (accumulation)",
    "whale positioning crowded long, longs paying funding (squeeze risk down) (skew +0.76)",
    "1 whale position(s) within 10% of liquidation",
    "HYPE lending: 3.40% supply / 6.10% borrow APR",
    "funding +0.0013%/hr"
  ],
  "hype_supply_apr": 3.4,
  "hype_borrow_apr": 6.1,
  "funding_rate": 1.25e-05,
  "whale_skew": 0.765,
  "net_flow_usd": 1900000.0
}
```

## Live mode

Get a key at [goldrush.dev](https://goldrush.dev) and export it:

```bash
export GOLDRUSH_API_KEY=cqt_...
hypersignal report          # full report: signal + every snapshot
hypersignal lending         # just the lending rates
hypersignal whales          # just whale positioning
hypersignal flows           # just the flow events
```

Edit the watchlist, thresholds, and tracked reserves in [`src/hypersignal/config.py`](src/hypersignal/config.py).

## As a service

```bash
hypersignal serve --offline            # http://127.0.0.1:8000/signal
# or, live:
GOLDRUSH_API_KEY=cqt_... hypersignal serve
```

Endpoints: `GET /signal`, `/report`, `/lending`, `/whales`, `/flows`, `/healthz`. Same JSON as the CLI and library.

## As a library

```python
from hypersignal import run, Settings

report = run(Settings.from_env(), offline=True)
print(report.signal.regime)            # "risk-on / choppy"
print(report.lending.by_symbol("USDe").borrow_apr_pct)
```

See [`examples/agent_consumer.py`](examples/agent_consumer.py) for a minimal allocation-agent loop.

## Dashboard

A custom **Vite + React** cockpit lives in [`dashboard/`](dashboard/) — a dark quant-terminal UI built for Harmonix's vault allocator: a regime verdict, a directional-bias gauge, the **agent directive** (ADD / HOLD / REDUCE / DE-RISK), and the three source panels each labelled with the GoldRush endpoint behind it.

```bash
# standalone — bundled real snapshot, no key needed
cd dashboard && npm install && npm run dev

# live — key stays server-side, dashboard proxies /api -> :8000
GOLDRUSH_API_KEY=cqt_... hypersignal serve      # terminal 1
cd dashboard && npm run dev                      # terminal 2
```

The API key never reaches the browser: the FastAPI backend holds it and the Vite dev server proxies `/api`.

### Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/dinxsh/hypersignal)

Vercel deploys the **static dashboard** via [`vercel.json`](vercel.json) (`buildCommand` builds `dashboard/`, output `dashboard/dist`). Out of the box the deployed site renders the **bundled real snapshot** committed at [`dashboard/src/sample-report.json`](dashboard/src/sample-report.json) — no key, no config, no backend. Import the repo and it just works.

```bash
npm i -g vercel
vercel            # import & deploy (uses vercel.json)
```

> Everything Python is excluded from the Vercel build (see [`.vercelignore`](.vercelignore)) because Vercel's Python backend auto-detection wants to deploy the whole repo as one FastAPI app, which conflicts with a static-SPA-plus-function layout.

**For live data on a hosted dashboard**, run the backend somewhere that handles long-lived Python (Render, Railway, Fly, or a VM) and point the dashboard at it:

```bash
# wherever you host it:
GOLDRUSH_API_KEY=cqt_... hypersignal serve        # exposes /report

# build the dashboard against that backend:
cd dashboard && VITE_API_URL=https://your-backend.example.com npm run build
```

The committed [`api/report.py`](api/report.py) (a serverless `handler`) and the FastAPI [`serve.py`](src/hypersignal/serve.py) both reuse the same engine, so you can host whichever fits your platform. The key always stays server-side; the browser only ever sees the report JSON.

## Scaling up

- **Whales:** `batchClearinghouseState` takes 50 wallets per call with **no rate limit**, so a watchlist of thousands is a tight loop. For push instead of poll, use the Streaming API [`walletTxs` firehose](https://goldrush.dev/docs/goldrush-hyperliquid/streaming/wallet-firehose).
- **Flows at firehose scale:** instead of polling per-wallet ledgers, stream every HyperCore deposit/withdrawal into your warehouse via the [Pipeline API HyperCore normalizers](https://goldrush.dev/docs/goldrush-pipeline-api/normalizers/hypercore) (`hl_deposits`, `hl_withdrawals`).

## Architecture

```
GoldRush Foundational API ─┐
  (HyperEVM log events)    ├─ lending.py ─┐
GoldRush Info API ─────────┤              ├─ signal.py ─→ RegimeSignal ─→ CLI / FastAPI / library
  (HyperCore state)        ├─ whales.py ──┤
  (HyperCore ledgers)      └─ flows.py ───┘
```

Each module is a pure parser (`parse_*`) plus a thin live fetcher (`fetch_*`). The parsers run identically on live responses and recorded fixtures, which is why `--offline` and the test suite exercise the real code path.

## Tests

```bash
pytest
```

## License

MIT. Built on [GoldRush](https://goldrush.dev). Not affiliated with Hyperliquid, HyperLend, or Felix; contract addresses are sourced from their public docs and may change.
