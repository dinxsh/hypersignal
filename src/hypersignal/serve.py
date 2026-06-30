"""FastAPI surface so an agent (or a dashboard) can poll the signal over HTTP.

    uvicorn hypersignal.serve:app        # live (needs GOLDRUSH_API_KEY)
    HYPERSIGNAL_OFFLINE=1 uvicorn ...     # offline fixtures

Every endpoint returns the same pydantic models the library produces, so the
JSON is identical whether consumed via CLI, library, or HTTP.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, TARGET_COIN
from .engine import run


def create_app(*, offline: bool | None = None) -> FastAPI:
    if offline is None:
        forced = os.environ.get("HYPERSIGNAL_OFFLINE", "").lower() in {"1", "true", "yes"}
        # Without a key, serve fixtures instead of erroring — so a fresh deploy
        # renders out of the box and only goes live once GOLDRUSH_API_KEY is set.
        offline = forced or not os.environ.get("GOLDRUSH_API_KEY")

    api = FastAPI(
        title="hypersignal",
        version="0.1.0",
        description="GoldRush-powered Hyperliquid regime signal for AI yield agents.",
    )

    # The Vite dashboard (and any browser client) calls this API cross-origin.
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    def _report(coin: str):
        return run(Settings.from_env(), offline=offline, coin=coin)

    @api.get("/signal")
    def signal(coin: str = TARGET_COIN):
        return _report(coin).signal

    @api.get("/report")
    def report(coin: str = TARGET_COIN):
        return _report(coin)

    @api.get("/lending")
    def lending(coin: str = TARGET_COIN):
        return _report(coin).lending

    @api.get("/whales")
    def whales(coin: str = TARGET_COIN):
        return _report(coin).whales

    @api.get("/flows")
    def flows(coin: str = TARGET_COIN):
        return _report(coin).flows

    @api.get("/healthz")
    def healthz():
        return {"ok": True, "mode": "offline" if offline else "live"}

    return api


# Module-level app for `uvicorn hypersignal.serve:app`.
app = create_app()
