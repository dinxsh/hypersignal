"""hypersignal command-line interface.

    hypersignal signal            # composite HYPE regime (default)
    hypersignal lending           # HyperEVM lending rates
    hypersignal whales            # HyperCore whale positioning
    hypersignal flows             # large HyperCore deposit/withdraw flows
    hypersignal serve             # FastAPI server exposing GET /signal

Add --offline to run against recorded fixtures (no API key needed).
"""
from __future__ import annotations

import typer

from .config import Settings, TARGET_COIN
from .engine import run

app = typer.Typer(add_completion=False, help="GoldRush-powered Hyperliquid signal engine.")

_offline = typer.Option(False, "--offline", help="Use recorded fixtures instead of the live GoldRush API.")
_coin = typer.Option(TARGET_COIN, "--coin", help="Perp coin to score.")


def _print(model) -> None:
    typer.echo(model.model_dump_json(indent=2))


@app.command()
def signal(offline: bool = _offline, coin: str = _coin) -> None:
    """Composite HYPE regime signal (lending + whales + flows)."""
    report = run(Settings.from_env(), offline=offline, coin=coin)
    _print(report.signal)


@app.command()
def report(offline: bool = _offline, coin: str = _coin) -> None:
    """Full report: the signal plus every underlying snapshot."""
    _print(run(Settings.from_env(), offline=offline, coin=coin))


@app.command()
def lending(offline: bool = _offline, coin: str = _coin) -> None:
    """HyperEVM lending rates (HYPE + stablecoins) from HyperLend."""
    _print(run(Settings.from_env(), offline=offline, coin=coin).lending)


@app.command()
def whales(offline: bool = _offline, coin: str = _coin) -> None:
    """HyperCore whale positioning for the target coin."""
    _print(run(Settings.from_env(), offline=offline, coin=coin).whales)


@app.command()
def flows(offline: bool = _offline, coin: str = _coin) -> None:
    """Large stablecoin/HYPE deposit and withdrawal flows on HyperCore."""
    _print(run(Settings.from_env(), offline=offline, coin=coin).flows)


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, offline: bool = _offline) -> None:
    """Run the FastAPI server (GET /signal, /report, /lending, /whales, /flows)."""
    import uvicorn

    from .serve import create_app

    uvicorn.run(create_app(offline=offline), host=host, port=port)


if __name__ == "__main__":
    app()
