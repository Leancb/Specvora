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
