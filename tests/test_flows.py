from hypersignal.flows import parse_flows


def test_parse_flows_nets_deposits_and_withdrawals(load_fixture, settings):
    snap = parse_flows(load_fixture("ledger_updates.json"), settings)
    assert snap.inflow_usd == 2_300_000.0
    assert snap.outflow_usd == 400_000.0
    assert snap.net_flow_usd == 1_900_000.0
    assert snap.direction == "accumulation"


def test_parse_flows_ignores_sub_threshold(load_fixture, settings):
    snap = parse_flows(load_fixture("ledger_updates.json"), settings)
    # the $5,000 deposit is below the 100k threshold -> 3 large events, not 4
    assert snap.large_event_count == 3
    assert all(e.usd >= settings.thresholds.large_flow_usd for e in snap.events)


def test_parse_flows_events_sorted_descending(load_fixture, settings):
    snap = parse_flows(load_fixture("ledger_updates.json"), settings)
    usds = [e.usd for e in snap.events]
    assert usds == sorted(usds, reverse=True)
    assert snap.events[0].usd == 1_500_000.0


def test_parse_flows_distribution_direction(settings):
    updates = {"0x1": [{"time": 1, "hash": "0x", "delta": {"type": "withdraw", "usdc": "500000"}}]}
    snap = parse_flows(updates, settings)
    assert snap.direction == "distribution"
    assert snap.net_flow_usd == -500_000.0
