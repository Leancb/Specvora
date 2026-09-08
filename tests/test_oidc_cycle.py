import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import httpx
from test_oidc_monitor import governed_trust
from test_oidc_trust import jwk, transport_for

from specvora.oidc_cycle import OidcMonitorCycleStore, run_oidc_monitor_cycle

NOW = datetime(2026, 9, 8, 12, tzinfo=UTC)


def cycle(tmp_path, discovered, *, alert_transport=None, token="t" * 32, cycle_id="cycle-1"):
    first = jwk("key-a")
    trust, audit = governed_trust(tmp_path, first)
    keys = discovered(first)
    return run_oidc_monitor_cycle(
        "https://identity.example/tenant/.well-known/openid-configuration",
        "https://identity.example/tenant", {"identity.example", "keys.example"},
        trust, audit, tmp_path, "https://alerts.example/oidc", {"alerts.example"},
        token, tmp_path / "state/oidc-monitor.db", cycle_id=cycle_id,
        now=NOW, discovery_transport=transport_for(keys),
        alert_transport=alert_transport,
    )


def test_lease_has_exactly_one_concurrent_owner(tmp_path):
    store = OidcMonitorCycleStore(tmp_path / "monitor.db", tmp_path)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(
            lambda owner: store.acquire("monitor", owner, NOW, 120),
            [f"owner-{index}" for index in range(8)],
        ))
    assert results.count(True) == 1


def test_expired_lease_can_be_reclaimed_but_wrong_owner_cannot_release(tmp_path):
    store = OidcMonitorCycleStore(tmp_path / "monitor.db", tmp_path)
    assert store.acquire("monitor", "first", NOW, 30)
    store.release("monitor", "wrong")
    assert not store.acquire("monitor", "second", NOW + timedelta(seconds=29), 30)
    assert store.acquire("monitor", "second", NOW + timedelta(seconds=30), 30)


def test_healthy_cycle_writes_history_without_contacting_receiver(tmp_path):
    requests = []
    result = cycle(
        tmp_path, lambda first: [first],
        alert_transport=httpx.MockTransport(lambda request: requests.append(request)),
    )
    assert result.status == "COMPLETED"
    assert result.delivery_status == "NO_ALERT"
    assert requests == []
    history = OidcMonitorCycleStore(
        tmp_path / "state/oidc-monitor.db", tmp_path
    ).history()
    assert history[0]["monitor_status"] == "HEALTHY"
    assert history[0]["delivery_status"] == "NO_ALERT"
    assert set(history[0]) == {
        "cycle_id", "observed_at", "monitor_status", "delivery_status", "alert_id",
        "report_sha256",
    }


def test_changed_provider_delivers_once_and_records_alert_id(tmp_path):
    requests = []

    def accept(request):
        requests.append(request)
        return httpx.Response(202)

    result = cycle(
        tmp_path, lambda first: [first, jwk("key-b")],
        alert_transport=httpx.MockTransport(accept),
    )
    assert result.status == "COMPLETED"
    assert result.monitor_status == "REVIEW_REQUIRED"
    assert result.delivery_status == "DELIVERED"
    assert len(requests) == 1
    history = OidcMonitorCycleStore(
        tmp_path / "state/oidc-monitor.db", tmp_path
    ).history()
    assert history[0]["alert_id"] == result.alert_id


def test_delivery_failure_is_recorded_generically_and_releases_lease(tmp_path):
    result = cycle(
        tmp_path, lambda first: [jwk("key-b")], token="secret-token-" * 3,
        alert_transport=httpx.MockTransport(
            lambda request: httpx.Response(400, text="remote secret")
        ),
    )
    assert result.status == "DELIVERY_FAILED"
    database = tmp_path / "state/oidc-monitor.db"
    store = OidcMonitorCycleStore(database, tmp_path)
    assert store.history()[0]["delivery_status"] == "DELIVERY_FAILED"
    assert store.acquire("oidc-trust-monitor", "replacement", NOW, 120)
    raw = database.read_bytes()
    assert b"secret-token" not in raw
    assert b"remote secret" not in raw


def test_active_cycle_is_skipped_without_history_or_network(tmp_path):
    database = tmp_path / "state/oidc-monitor.db"
    store = OidcMonitorCycleStore(database, tmp_path)
    assert store.acquire("oidc-trust-monitor", "other-owner", NOW, 120)
    result = run_oidc_monitor_cycle(
        "https://not-contacted.example/discovery", "https://identity.example/tenant",
        {"not-contacted.example"}, tmp_path / "missing.json", tmp_path / "missing.jsonl",
        tmp_path, "https://alerts.example/oidc", {"alerts.example"}, "t" * 32,
        database, now=NOW,
    )
    assert result.status == "SKIPPED_LEASE"
    assert store.history() == []


def test_state_path_and_history_contract_are_bounded(tmp_path):
    try:
        OidcMonitorCycleStore(tmp_path.parent / "outside.db", tmp_path)
    except ValueError as error:
        assert "escapes" in str(error)
    else:
        raise AssertionError("state database outside workspace was accepted")
    store = OidcMonitorCycleStore(tmp_path / "monitor.db", tmp_path)
    assert json.dumps(store.history()) == "[]"
