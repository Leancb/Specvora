from datetime import UTC, datetime, timedelta

import httpx
import pytest

from specvora.portal_session_store import HttpPortalSessionStore


def test_http_state_contract_and_secret_transport():
    requests = []
    def handler(request):
        requests.append(request)
        if request.url.path == "/v1/oidc-transaction-claims":
            return httpx.Response(200, json={"nonce": "n", "code_verifier": "v"})
        if request.url.path == "/v1/mfa-claims":
            return httpx.Response(201)
        if request.method == "POST":
            return httpx.Response(201)
        if request.method == "GET":
            return httpx.Response(200, json={"active": True})
        return httpx.Response(204)

    store = HttpPortalSessionStore("https://state.example", "s" * 32,
                                   transport=httpx.MockTransport(handler))
    now = datetime.now(UTC)
    store.register_oidc_transaction("a" * 64, "n" * 32, "v" * 43,
                                    now + timedelta(minutes=5))
    assert store.claim_oidc_transaction("a" * 64, now) == ("n", "v")
    assert store.claim_mfa_counter("user", 4)
    assert store.claim_login_attempt("a" * 64, now, 5, 300)
    store.clear_login_attempts("a" * 64)
    store.replace_recovery_codes("user", ["b" * 64])
    assert store.claim_recovery_code("user", "b" * 64)
    store.record_security_event("recovery_used", "c" * 64, now)
    store.register_session("id", "user", now + timedelta(minutes=5))
    assert store.session_is_active("id", now)
    store.revoke_session("id")
    assert all(r.headers["authorization"] == "Bearer " + "s" * 32 for r in requests)


def test_http_state_requires_safe_configuration():
    with pytest.raises(ValueError, match="HTTPS"):
        HttpPortalSessionStore("http://state.example", "s" * 32)
    with pytest.raises(ValueError, match="token"):
        HttpPortalSessionStore("https://state.example", "short")


def test_http_state_rejects_invalid_oidc_claim_response():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"nonce": "n"}))
    store = HttpPortalSessionStore("https://state.example", "s" * 32, transport=transport)
    with pytest.raises(RuntimeError, match="invalid response"):
        store.claim_oidc_transaction("a" * 64, datetime.now(UTC))
