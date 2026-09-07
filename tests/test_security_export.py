import json
from datetime import UTC, datetime

import httpx
import pytest

from specvora.portal_session_store import PortalSessionStore
from specvora.security_export import export_security_events


def populated_state(tmp_path):
    path = tmp_path / "state.db"
    store = PortalSessionStore(path)
    now = datetime(2026, 9, 7, tzinfo=UTC)
    store.record_security_event("login_failed", "a" * 64, now)
    store.record_security_event("login_succeeded", "b" * 64, now)
    return path


def test_export_is_incremental_authenticated_and_idempotent(tmp_path):
    state = populated_state(tmp_path)
    checkpoint = tmp_path / "checkpoint.json"
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(202)

    result = export_security_events(
        state, checkpoint, "https://siem.example/events", ["siem.example"], "t" * 32,
        transport=httpx.MockTransport(handler), sleeper=lambda _: None,
    )
    assert result["exported"] == 2
    assert json.loads(checkpoint.read_text())["last_event_id"] == 2
    request = requests[0]
    assert request.headers["authorization"] == "Bearer " + "t" * 32
    assert request.headers["idempotency-key"] == result["batch_id"]
    payload = json.loads(request.content)
    assert set(payload) == {"version", "events"}
    assert set(payload["events"][0]) == {"event_id", "event_type", "subject", "occurred_at"}
    assert ("t" * 32).encode() not in request.content
    again = export_security_events(
        state, checkpoint, "https://siem.example/events", ["siem.example"], "t" * 32,
        transport=httpx.MockTransport(lambda _: pytest.fail("No duplicate network request")),
    )
    assert again == {"status": "NO_EVENTS", "exported": 0, "last_event_id": 2}


def test_export_retries_transient_failure_without_advancing_checkpoint(tmp_path):
    state = populated_state(tmp_path)
    checkpoint = tmp_path / "checkpoint.json"
    statuses = iter([503, 429, 202])
    delays = []
    result = export_security_events(
        state, checkpoint, "https://siem.example/events", ["siem.example"], "t" * 32,
        transport=httpx.MockTransport(lambda _: httpx.Response(next(statuses))),
        sleeper=delays.append,
    )
    assert result["exported"] == 2
    assert delays == [1.0, 2.0]

    failed_checkpoint = tmp_path / "failed.json"
    with pytest.raises(RuntimeError, match="did not accept"):
        export_security_events(
            state, failed_checkpoint, "https://siem.example/events", ["siem.example"], "t" * 32,
            transport=httpx.MockTransport(lambda _: httpx.Response(503)), sleeper=lambda _: None,
        )
    assert not failed_checkpoint.exists()


@pytest.mark.parametrize(
    ("endpoint", "hosts", "token"),
    [
        ("http://siem.example/events", ["siem.example"], "t" * 32),
        ("https://siem.example/events", ["other.example"], "t" * 32),
        ("https://user@siem.example/events", ["siem.example"], "t" * 32),
        ("https://siem.example/events", ["siem.example"], "short"),
    ],
)
def test_export_rejects_unsafe_destination_and_token(tmp_path, endpoint, hosts, token):
    with pytest.raises(ValueError):
        export_security_events(populated_state(tmp_path), tmp_path / "checkpoint.json",
                               endpoint, hosts, token)
