from hypersignal.lending import (
    RESERVE_DATA_UPDATED_TOPIC,
    parse_lending,
)


def test_topic_is_canonical_aave_v3():
    # The well-known Aave v3 ReserveDataUpdated topic0.
    assert RESERVE_DATA_UPDATED_TOPIC == (
        "0x804c9b842b2748a22bb64b345453a3de7ca54a6ca45ce00d415894979e22897a"
    )


def test_parse_lending_keeps_latest_per_reserve(load_fixture):
    snap = parse_lending(load_fixture("lending_events.json"))
    whype = snap.by_symbol("wHYPE")
    assert whype is not None
    # later block (3.4/6.1) wins over the stale 2.9/5.2 event
    assert whype.supply_apr_pct == 3.4
    assert whype.borrow_apr_pct == 6.1
    assert whype.block_height == 9_050_000


def test_parse_lending_decodes_stablecoins(load_fixture):
    snap = parse_lending(load_fixture("lending_events.json"))
    usde = snap.by_symbol("USDe")
    assert usde.kind == "stable"
    assert usde.supply_apr_pct == 8.2
    assert usde.borrow_apr_pct == 11.5


def test_parse_lending_handles_goldrush_decoded_events():
    # When GoldRush returns the event already decoded, we use decoded.params.
    ray = 10**27
    events = [
        {
            "block_height": 100,
            "block_signed_at": "2026-06-30T00:00:00Z",
            "decoded": {
                "name": "ReserveDataUpdated",
                "params": [
                    {"name": "reserve", "value": "0x5555555555555555555555555555555555555555"},
                    {"name": "liquidityRate", "value": str(int(0.05 * ray))},
                    {"name": "stableBorrowRate", "value": "0"},
                    {"name": "variableBorrowRate", "value": str(int(0.09 * ray))},
                    {"name": "liquidityIndex", "value": str(ray)},
                    {"name": "variableBorrowIndex", "value": str(ray)},
                ],
            },
        }
    ]
    snap = parse_lending(events)
    whype = snap.by_symbol("wHYPE")
    assert whype.supply_apr_pct == 5.0
    assert whype.borrow_apr_pct == 9.0


def test_parse_lending_ignores_unrelated_events():
    events = [{"block_height": 1, "raw_log_topics": ["0xdeadbeef"], "raw_log_data": "0x"}]
    assert parse_lending(events).reserves == []
