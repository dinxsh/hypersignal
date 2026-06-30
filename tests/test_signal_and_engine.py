import httpx

from hypersignal.config import Settings
from hypersignal.engine import run
from hypersignal.goldrush import FoundationalClient, GoldRushError, InfoClient


def test_offline_report_is_deterministic(settings):
    report = run(settings, offline=True)
    assert report.mode == "offline"
    sig = report.signal
    assert sig.coin == "HYPE"
    assert sig.directional_bias == 0.876
    assert sig.volatility_score == 0.571
    assert sig.regime == "risk-on / choppy"
    assert sig.hype_borrow_apr == 6.1


def test_live_run_without_key_raises():
    try:
        run(Settings(api_key=""), offline=False)
    except RuntimeError as exc:
        assert "GOLDRUSH_API_KEY" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError when no API key is set")


def test_foundational_client_unwraps_data_envelope():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer k"
        return httpx.Response(200, json={"data": {"items": [{"block_height": 1}]}, "error": False})

    client = FoundationalClient("k", client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://x"))
    items = client.log_events_by_contract("hyperevm-mainnet", "0xpool")
    assert items == [{"block_height": 1}]


def test_foundational_client_raises_on_error_envelope():
    def handler(request):
        return httpx.Response(200, json={"data": None, "error": True, "error_message": "bad chain"})

    client = FoundationalClient("k", client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://x"))
    try:
        client.token_balances("nope", "0x1")
    except GoldRushError as exc:
        assert "bad chain" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected GoldRushError")


def test_info_client_posts_type_and_returns_payload():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=[{"user": "0x1", "assetPositions": []}])

    client = InfoClient("k", client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://x"))
    out = client.batch_clearinghouse_state(["0x1"])
    assert seen["body"]["type"] == "batchClearinghouseState"
    assert out[0]["user"] == "0x1"


def test_batch_clearinghouse_state_rejects_too_many():
    client = InfoClient("k", client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[])), base_url="https://x"))
    try:
        client.batch_clearinghouse_state(["0x"] * 51)
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for >50 wallets")
