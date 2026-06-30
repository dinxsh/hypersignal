"""Thin GoldRush API clients.

Two surfaces, two clients:

* ``FoundationalClient`` -> ``api.covalenthq.com`` REST, for HyperEVM on-chain
  data (token balances, transfers, decoded/raw log events).
* ``InfoClient`` -> ``hypercore.goldrushdata.com/info``, a drop-in, rate-limit
  free replacement for the public Hyperliquid ``/info`` API.

Both accept an injected ``httpx`` client so tests can supply a mock transport
and the rest of the codebase never touches the network directly.

Docs:
* https://goldrush.dev/docs/chains/hyperevm
* https://goldrush.dev/docs/goldrush-hyperliquid/info-api/overview
"""
from __future__ import annotations

from typing import Any

import httpx

from .config import FOUNDATIONAL_BASE_URL, INFO_BASE_URL


class GoldRushError(RuntimeError):
    """Raised when the GoldRush API returns an error payload or HTTP error."""


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}


class FoundationalClient:
    """GoldRush Foundational API (REST) over HyperEVM."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = FOUNDATIONAL_BASE_URL,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)
        self._client.headers.update(_auth_headers(api_key))

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._client.get(path, params={k: v for k, v in (params or {}).items() if v is not None})
        if resp.status_code >= 400:
            raise GoldRushError(f"GET {path} -> {resp.status_code}: {resp.text[:300]}")
        body = resp.json()
        # Foundational responses wrap payloads as {"data": ..., "error": bool, ...}
        if isinstance(body, dict) and body.get("error"):
            raise GoldRushError(f"GET {path} -> {body.get('error_message') or body}")
        return body.get("data", body) if isinstance(body, dict) else body

    def log_events_by_contract(
        self,
        chain: str,
        contract: str,
        *,
        starting_block: int | None = None,
        ending_block: int | None = None,
        page_size: int = 1000,
    ) -> list[dict[str, Any]]:
        """Decoded + raw log events emitted by ``contract``."""
        data = self._get(
            f"/{chain}/events/address/{contract}/",
            {
                "starting-block": starting_block,
                "ending-block": ending_block,
                "page-size": page_size,
            },
        )
        return data.get("items", [])

    def latest_block(self, chain: str) -> int:
        data = self._get(f"/{chain}/block_v2/latest/")
        items = data.get("items", [])
        return int(items[0]["height"]) if items else 0

    def token_balances(self, chain: str, address: str, *, quote_currency: str = "USD") -> list[dict[str, Any]]:
        data = self._get(
            f"/{chain}/address/{address}/balances_v2/",
            {"quote-currency": quote_currency},
        )
        return data.get("items", [])

    def close(self) -> None:
        self._client.close()


class InfoClient:
    """GoldRush Hyperliquid Info API (POST /info) over HyperCore."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = INFO_BASE_URL,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)
        self._client.headers.update({**_auth_headers(api_key), "Content-Type": "application/json"})

    def info(self, body: dict[str, Any]) -> Any:
        resp = self._client.post("/info", json=body)
        if resp.status_code >= 400:
            raise GoldRushError(f"POST /info {body.get('type')} -> {resp.status_code}: {resp.text[:300]}")
        payload = resp.json()
        if isinstance(payload, dict) and payload.get("error"):
            raise GoldRushError(f"POST /info {body.get('type')} -> {payload}")
        return payload

    # --- typed convenience wrappers over the wire-compatible `type` values ---
    def meta_and_asset_ctxs(self) -> Any:
        """Tuple [meta, assetCtxs[]] -- perp universe + live mark/funding/OI."""
        return self.info({"type": "metaAndAssetCtxs", "dex": ""})

    def batch_clearinghouse_state(self, users: list[str]) -> list[dict[str, Any]]:
        """Perp account state for 1-50 wallets in one call (GoldRush-native)."""
        if not 1 <= len(users) <= 50:
            raise ValueError("batchClearinghouseState accepts 1-50 wallets per call")
        return self.info({"type": "batchClearinghouseState", "users": users})

    def user_non_funding_ledger_updates(self, user: str, start_time_ms: int) -> list[dict[str, Any]]:
        """Deposits, withdrawals, transfers and vault flows since start_time_ms."""
        return self.info(
            {"type": "userNonFundingLedgerUpdates", "user": user, "startTime": start_time_ms}
        )

    def candle_snapshot(self, coin: str, interval: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        """Historical OHLCV candles for a coin/interval window."""
        return self.info(
            {"type": "candleSnapshot", "req": {"coin": coin, "interval": interval, "startTime": start_ms, "endTime": end_ms}}
        )

    def l2_book(self, coin: str) -> dict[str, Any]:
        """Aggregated L2 order book snapshot for one coin."""
        return self.info({"type": "l2Book", "coin": coin})

    def user_fills(self, user: str) -> list[dict[str, Any]]:
        """Most recent fills for a wallet (up to 2,000)."""
        return self.info({"type": "userFills", "user": user})

    def close(self) -> None:
        self._client.close()
