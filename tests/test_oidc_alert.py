import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from specvora.oidc_alert import deliver_oidc_alert
from specvora.oidc_monitor import OidcTrustMonitorReport


def report(status="REVIEW_REQUIRED", *, checked_at=None):
    return OidcTrustMonitorReport(
        status=status, issuer="https://identity.example/tenant",
        current_jwks_sha256="a" * 64, discovered_jwks_sha256="b" * 64,
        current_key_ids=["key-a"], discovered_key_ids=["key-a", "key-b"],
        findings=[] if status == "HEALTHY" else ["PROVIDER_KEYS_CHANGED"],
        checked_at=checked_at or datetime(2026, 9, 7, tzinfo=UTC),
    )


def test_healthy_report_does_not_contact_receiver():
    calls = []
    result = deliver_oidc_alert(
        report("HEALTHY"), "https://alerts.example/oidc", {"alerts.example"}, "t" * 32,
        transport=httpx.MockTransport(lambda request: calls.append(request)),
    )
    assert result == {"status": "NO_ALERT", "alert_id": None, "attempts": 0}
    assert calls == []


def test_alert_is_authenticated_bounded_and_idempotent():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(503 if len(requests) == 1 else 202)

    pauses = []
    first = deliver_oidc_alert(
        report(), "https://alerts.example/v1/oidc", {"alerts.example"}, "t" * 32,
        transport=httpx.MockTransport(handler), sleeper=pauses.append,
    )
    later = deliver_oidc_alert(
        report(checked_at=datetime(2026, 9, 7, tzinfo=UTC) + timedelta(hours=1)),
        "https://alerts.example/v1/oidc", {"alerts.example"}, "t" * 32,
        transport=httpx.MockTransport(lambda request: httpx.Response(202)),
    )
    assert first["status"] == "DELIVERED"
    assert first["attempts"] == 2
    assert first["alert_id"] == later["alert_id"]
    assert pauses == [1.0]
    assert all(request.headers["authorization"] == "Bearer " + "t" * 32
               for request in requests)
    assert all(request.headers["idempotency-key"] == first["alert_id"]
               for request in requests)
    payload = json.loads(requests[-1].content)
    assert payload["version"] == "specvora-oidc-alert-v1"
    assert payload["severity"] == "WARNING"
    assert set(payload) == {
        "version", "alert_id", "severity", "observed_at", "status", "issuer",
        "current_jwks_sha256", "discovered_jwks_sha256", "current_key_ids",
        "discovered_key_ids", "findings",
    }


def test_blocked_alert_is_critical():
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(204)

    blocked = report("BLOCKED").model_copy(update={"findings": ["TRUST_DISCONTINUITY"]})
    deliver_oidc_alert(
        blocked, "https://alerts.example/oidc", {"alerts.example"}, "t" * 32,
        transport=httpx.MockTransport(handler),
    )
    assert captured[0]["severity"] == "CRITICAL"


@pytest.mark.parametrize(
    ("endpoint", "hosts", "token"),
    [
        ("http://alerts.example/oidc", {"alerts.example"}, "t" * 32),
        ("https://evil.example/oidc", {"alerts.example"}, "t" * 32),
        ("https://alerts.example/oidc", {"alerts.example"}, "short"),
    ],
)
def test_unsafe_delivery_configuration_is_rejected(endpoint, hosts, token):
    with pytest.raises(ValueError):
        deliver_oidc_alert(report(), endpoint, hosts, token)


def test_receiver_failure_is_generic_and_never_leaks_token():
    with pytest.raises(RuntimeError, match="did not accept") as failure:
        deliver_oidc_alert(
            report(), "https://alerts.example/oidc", {"alerts.example"}, "secret-token-" * 3,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(400, text="remote-secret-details")
            ),
        )
    assert "secret-token" not in str(failure.value)
    assert "remote-secret" not in str(failure.value)
