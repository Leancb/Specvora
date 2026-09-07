import json

import pytest
from fastapi.testclient import TestClient
from test_portal import workspace

import specvora.main as main_module
from specvora.main import app
from specvora.oidc import OidcClaims
from specvora.portal_auth import hash_password, totp_code


@pytest.fixture
def authenticated_portal(tmp_path, monkeypatch):
    users = tmp_path / "auth/users.json"
    users.parent.mkdir()
    users.write_text(
        json.dumps(
            {
                "users": [
                    {
                        "username": "reviewer.one",
                        "display_name": "Reviewer One",
                        "roles": ["reviewer"],
                        "password_hash": hash_password("reviewer-password-long"),
                    },
                    {
                        "username": "operator.one",
                        "display_name": "Operator One",
                        "roles": ["operator"],
                        "password_hash": hash_password("operator-password-long"),
                    },
                    {
                        "username": "mfa.one",
                        "display_name": "MFA One",
                        "roles": ["viewer"],
                        "password_hash": hash_password("mfa-password-long"),
                        "totp_secret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    key = tmp_path / "auth/session.key"
    key.write_bytes(b"s" * 32)
    monkeypatch.setenv("SPECVORA_PORTAL_AUTH_MODE", "required")
    monkeypatch.setenv("SPECVORA_PORTAL_USERS_FILE", str(users))
    monkeypatch.setenv("SPECVORA_PORTAL_SESSION_KEY", str(key))
    monkeypatch.setenv("SPECVORA_PORTAL_STATE_DB", str(tmp_path / "auth/session-state.db"))
    monkeypatch.setenv("SPECVORA_PORTAL_COOKIE_SECURE", "false")
    monkeypatch.setenv("SPECVORA_DB_PATH", str(tmp_path / "state/specvora.db"))
    return TestClient(app)


def login(client: TestClient, username: str, password: str) -> dict:
    response = client.post("/api/session", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def test_login_cookie_and_read_authorization(authenticated_portal):
    client = authenticated_portal
    assert client.get("/api/projects").status_code == 401
    assert (
        client.post(
            "/api/session", json={"username": "reviewer.one", "password": "incorrect"}
        ).status_code
        == 401
    )
    identity = login(client, "reviewer.one", "reviewer-password-long")
    cookie = client.cookies.get("specvora_session")
    assert cookie
    assert identity["roles"] == ["reviewer"]
    assert client.get("/api/projects").status_code == 200
    csrf = identity["csrf_token"]
    assert client.delete("/api/session", headers={"X-Specvora-CSRF": csrf}).status_code == 204
    assert client.get("/api/projects").status_code == 401


def test_login_requires_mfa_and_rejects_reused_code(authenticated_portal):
    client = authenticated_portal
    payload = {"username": "mfa.one", "password": "mfa-password-long"}
    assert client.post("/api/session", json=payload).status_code == 401
    payload["totp_code"] = totp_code("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ")
    assert client.post("/api/session", json=payload).status_code == 200
    assert client.post("/api/session", json=payload).status_code == 401


def test_oidc_routes_issue_local_revocable_session(authenticated_portal, monkeypatch):
    client = authenticated_portal
    monkeypatch.setenv("SPECVORA_OIDC_AUTHORIZATION_ENDPOINT",
                       "https://identity.example/authorize")
    monkeypatch.setenv("SPECVORA_OIDC_TOKEN_ENDPOINT", "https://identity.example/token")
    monkeypatch.setenv("SPECVORA_OIDC_CLIENT_ID", "specvora")
    monkeypatch.setenv("SPECVORA_OIDC_REDIRECT_URI",
                       "http://127.0.0.1:8102/api/session/oidc/callback")
    monkeypatch.setenv("SPECVORA_OIDC_TOKEN_ALLOWED_HOSTS", "identity.example")
    calls = []

    def begin(store, authorization, client_id, redirect_uri):
        calls.append((store, authorization, client_id, redirect_uri))
        return "https://identity.example/authorize?state=browser-state"

    def complete(store, state, code, token_endpoint, client_id, redirect_uri, hosts):
        calls.append((store, state, code, token_endpoint, client_id, redirect_uri, hosts))
        return OidcClaims(
            iss="https://identity.example/tenant", aud="specvora", sub="subject-1",
            exp=2_000_000_000, iat=1_000_000_000, nonce="nonce-value-long-enough",
            preferred_username="reviewer.one",
        )

    monkeypatch.setattr(main_module, "begin_oidc_login", begin)
    monkeypatch.setattr(main_module, "complete_oidc_login", complete)
    start = client.get("/api/session/oidc/start", follow_redirects=False)
    assert start.status_code == 303
    assert start.headers["location"].startswith("https://identity.example/authorize")
    callback = client.get(
        "/api/session/oidc/callback?state=browser-state&code=authorization-code",
        follow_redirects=False,
    )
    assert callback.status_code == 303
    assert callback.headers["location"] == "/portal"
    assert client.cookies.get("specvora_session")
    assert client.get("/api/projects").status_code == 200
    assert calls[1][1:3] == ("browser-state", "authorization-code")
    identity = client.get("/api/session").json()
    assert identity["username"] == "reviewer.one"
    assert identity["roles"] == ["reviewer"]


def test_oidc_callback_failure_is_generic(authenticated_portal):
    response = authenticated_portal.get(
        "/api/session/oidc/callback?error=access_denied&error_description=provider-secret",
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "OIDC login failed"}
    assert "provider-secret" not in response.text


def test_oidc_start_fails_closed_when_configuration_is_incomplete(authenticated_portal):
    response = authenticated_portal.get("/api/session/oidc/start", follow_redirects=False)
    assert response.status_code == 503
    assert response.json() == {"detail": "OIDC login is unavailable"}


def test_roles_csrf_and_reviewer_identity_are_enforced(
    authenticated_portal, tmp_path
):
    client = authenticated_portal
    project_file, proposal_file = workspace(tmp_path)
    reviewer = login(client, "reviewer.one", "reviewer-password-long")
    project = {"project_file": str(project_file), "workspace_root": str(tmp_path)}
    assert (
        client.post(
            "/api/projects",
            json=project,
            headers={"X-Specvora-CSRF": reviewer["csrf_token"]},
        ).status_code
        == 403
    )
    operator = login(client, "operator.one", "operator-password-long")
    assert client.post("/api/projects", json=project).status_code == 403
    assert (
        client.post(
            "/api/projects",
            json=project,
            headers={"X-Specvora-CSRF": operator["csrf_token"]},
        ).status_code
        == 201
    )
    review = {
        "review_id": "auth-review",
        "project_id": "portal-demo",
        "proposal_file": str(proposal_file),
    }
    assert (
        client.post(
            "/api/reviews",
            json=review,
            headers={"X-Specvora-CSRF": operator["csrf_token"]},
        ).status_code
        == 201
    )
    reviewer = login(client, "reviewer.one", "reviewer-password-long")
    decision = {
        "reviewer": "Someone Else",
        "approval": "APPROVED_PROPOSAL_PROMOTION",
        "decisions": [
            {"proposal_id": "AI-001", "decision": "ACCEPT", "rationale": "Reviewed"}
        ],
    }
    url = "/api/reviews/auth-review/approval-payload"
    headers = {"X-Specvora-CSRF": reviewer["csrf_token"]}
    rejected = client.post(url, json=decision, headers=headers)
    assert rejected.status_code == 400
    assert "authenticated identity" in rejected.json()["detail"]
    decision["reviewer"] = "Reviewer One"
    assert client.post(url, json=decision, headers=headers).status_code == 200
