from hypersignal.whales import extract_market, parse_whales


def test_extract_market_finds_target_coin(load_fixture):
    market = extract_market(load_fixture("meta_and_asset_ctxs.json"), "HYPE")
    assert market.mark_price == 38.5
    assert market.funding_rate == 0.0000125
    assert market.open_interest == 5_200_000.0


def test_parse_whales_aggregates_positioning(load_fixture, settings):
    snap = parse_whales(
        load_fixture("meta_and_asset_ctxs.json"),
        load_fixture("batch_clearinghouse_state.json"),
        settings,
    )
    # 3 valid wallets with a HYPE position (4th slot is an upstream error)
    assert snap.wallets_with_position == 3
    assert snap.long_notional_usd == 5_775_000.0
    assert snap.short_notional_usd == 770_000.0
    assert snap.net_notional_usd == 5_005_000.0
    assert round(snap.skew, 2) == 0.76
    assert snap.crowded is True
    assert snap.near_liquidation == 1  # the 36.0 liq px wallet, ~6.5% from mark
    assert "squeeze risk down" in snap.positioning


def test_parse_whales_skips_error_slots(settings):
    meta = [{"universe": [{"name": "HYPE"}]}, [{"markPx": "10", "funding": "0", "openInterest": "0", "dayNtlVlm": "0"}]]
    states = [{"error": "upstream_error", "user": "0x1"}]
    snap = parse_whales(meta, states, settings)
    assert snap.wallets_with_position == 0
    assert snap.skew == 0.0
