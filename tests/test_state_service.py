import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from specvora.state_service import app


def configured_client(tmp_path, monkeypatch):
    monkeypatch.setenv("SPECVORA_STATE_SERVICE_TOKEN", "t" * 32)
    monkeypatch.setenv("SPECVORA_STATE_SERVICE_DB", str(tmp_path / "state.db"))
    return TestClient(app), {"Authorization": "Bearer " + "t" * 32}


def test_service_requires_authentication_and_persists_session(tmp_path, monkeypatch):
    client, headers = configured_client(tmp_path, monkeypatch)
    assert client.get("/health").status_code == 200
    unauthenticated = client.post(
        "/v1/mfa-claims", json={"username": "user.one", "counter": 7}
    )
    assert unauthenticated.status_code == 401
    assert client.post("/v1/mfa-claims", headers=headers,
                       json={"username": "user.one", "counter": 7}).status_code == 201
    assert client.post("/v1/mfa-claims", headers=headers,
                       json={"username": "user.one", "counter": 7}).status_code == 409
    expires = datetime.now(UTC) + timedelta(minutes=5)
    payload = {"session_id": "session-identifier-1", "username": "user.one",
               "expires_at": expires.isoformat()}
    assert client.post("/v1/sessions", headers=headers, json=payload).status_code == 201
    params = {"at": datetime.now(UTC).isoformat()}
    assert client.get("/v1/sessions/session-identifier-1", headers=headers,
                      params=params).json() == {"active": True}
    assert client.delete("/v1/sessions/session-identifier-1", headers=headers).status_code == 204
    assert client.get("/v1/sessions/session-identifier-1", headers=headers,
                      params=params).json() == {"active": False}


def test_service_mfa_claim_is_atomic_under_concurrency(tmp_path, monkeypatch):
    client, headers = configured_client(tmp_path, monkeypatch)
    def claim(_):
        return client.post("/v1/mfa-claims", headers=headers,
                           json={"username": "user.one", "counter": 9}).status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses = list(pool.map(claim, range(4)))
    assert statuses.count(201) == 1
    assert statuses.count(409) == 3


def test_service_fails_closed_without_storage(tmp_path, monkeypatch):
    client, headers = configured_client(tmp_path, monkeypatch)
    monkeypatch.delenv("SPECVORA_STATE_SERVICE_DB")
    response = client.post("/v1/mfa-claims", headers=headers,
                           json={"username": "user.one", "counter": 1})
    assert response.status_code == 503


def test_service_enforces_and_clears_login_attempt_limit(tmp_path, monkeypatch):
    client, headers = configured_client(tmp_path, monkeypatch)
    subject = "a" * 64
    payload = {
        "subject": subject,
        "observed_at": datetime.now(UTC).isoformat(),
        "limit": 2,
        "window_seconds": 300,
    }
    assert client.post("/v1/login-attempts", headers=headers, json=payload).status_code == 201
    assert client.post("/v1/login-attempts", headers=headers, json=payload).status_code == 201
    assert client.post("/v1/login-attempts", headers=headers, json=payload).status_code == 429
    assert client.delete(f"/v1/login-attempts/{subject}", headers=headers).status_code == 204
    assert client.post("/v1/login-attempts", headers=headers, json=payload).status_code == 201


def test_service_accepts_only_active_hashed_keyring_tokens(tmp_path, monkeypatch):
    client, _headers = configured_client(tmp_path, monkeypatch)
    now = datetime.now(UTC)
    current = "current-rotating-state-service-token"
    overlap = "overlap-rotating-state-service-token-1"
    previous = "previous-rotating-state-service-token"
    future = "future-rotating-state-service-token-1"
    trust = {
        "version": "specvora-state-service-trust-v1",
        "tokens": [
            {
                "token_sha256": hashlib.sha256(current.encode()).hexdigest(),
                "not_before": (now - timedelta(minutes=1)).isoformat(),
                "expires_at": (now + timedelta(minutes=5)).isoformat(),
            },
            {
                "token_sha256": hashlib.sha256(overlap.encode()).hexdigest(),
                "not_before": (now - timedelta(minutes=1)).isoformat(),
                "expires_at": (now + timedelta(minutes=1)).isoformat(),
            },
            {
                "token_sha256": hashlib.sha256(previous.encode()).hexdigest(),
                "not_before": (now - timedelta(minutes=10)).isoformat(),
                "expires_at": (now - timedelta(minutes=1)).isoformat(),
            },
            {
                "token_sha256": hashlib.sha256(future.encode()).hexdigest(),
                "not_before": (now + timedelta(minutes=1)).isoformat(),
                "expires_at": (now + timedelta(minutes=10)).isoformat(),
            },
        ],
    }
    trust_file = tmp_path / "service-trust.json"
    trust_file.write_text(json.dumps(trust), encoding="utf-8")
    monkeypatch.setenv("SPECVORA_STATE_SERVICE_TOKEN_FILE", str(trust_file))
    endpoint = "/v1/mfa-claims"
    payload = {"username": "user.one", "counter": 20}
    assert client.post(endpoint, headers={"Authorization": f"Bearer {current}"},
                       json=payload).status_code == 201
    payload["counter"] = 21
    assert client.post(endpoint, headers={"Authorization": f"Bearer {overlap}"},
                       json=payload).status_code == 201
    assert client.post(endpoint, headers={"Authorization": f"Bearer {previous}"},
                       json=payload).status_code == 401
    assert client.post(endpoint, headers={"Authorization": f"Bearer {future}"},
                       json=payload).status_code == 401


def test_service_keyring_fails_closed_on_invalid_configuration(tmp_path, monkeypatch):
    client, headers = configured_client(tmp_path, monkeypatch)
    trust_file = tmp_path / "service-trust.json"
    trust_file.write_text('{"version":"wrong","tokens":[]}', encoding="utf-8")
    monkeypatch.setenv("SPECVORA_STATE_SERVICE_TOKEN_FILE", str(trust_file))
    response = client.post("/v1/mfa-claims", headers=headers,
                           json={"username": "user.one", "counter": 30})
    assert response.status_code == 401
    assert "wrong" not in response.text
