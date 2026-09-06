import json
from datetime import UTC, datetime, timedelta

import pytest

from specvora.portal_auth import (
    PortalUser,
    SessionIdentity,
    authenticate,
    hash_password,
    issue_session,
    require_capability,
    verify_password,
    verify_session,
)


@pytest.fixture
def configured_auth(tmp_path, monkeypatch):
    key = tmp_path / "session.key"
    key.write_bytes(b"k" * 32)
    users = tmp_path / "users.json"
    users.write_text(
        json.dumps(
            {
                "users": [
                    {
                        "username": "reviewer.one",
                        "display_name": "Reviewer One",
                        "roles": ["reviewer"],
                        "password_hash": hash_password("correct horse battery staple"),
                        "active": True,
                        "session_version": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SPECVORA_PORTAL_AUTH_MODE", "required")
    monkeypatch.setenv("SPECVORA_PORTAL_SESSION_KEY", str(key))
    monkeypatch.setenv("SPECVORA_PORTAL_USERS_FILE", str(users))
    return users


def test_password_hash_is_salted_and_verified():
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)
    assert "correct horse" not in first


def test_session_is_signed_expires_and_reloads_current_roles(configured_auth):
    now = datetime(2026, 9, 6, tzinfo=UTC)
    user = authenticate("reviewer.one", "correct horse battery staple")
    token, identity = issue_session(user, now=now)
    assert verify_session(token, now=now + timedelta(minutes=1)).username == "reviewer.one"
    assert identity.roles == ["reviewer"]
    with pytest.raises(ValueError, match="invalid or expired"):
        verify_session(token + "x", now=now)
    with pytest.raises(ValueError, match="invalid or expired"):
        verify_session(token, now=now + timedelta(minutes=31))


def test_disabled_user_and_session_version_revoke_access(configured_auth):
    user = authenticate("reviewer.one", "correct horse battery staple")
    token, _ = issue_session(user)
    data = json.loads(configured_auth.read_text(encoding="utf-8"))
    data["users"][0]["session_version"] = 2
    configured_auth.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid or expired"):
        verify_session(token)
    data["users"][0]["active"] = False
    configured_auth.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="credentials"):
        authenticate("reviewer.one", "correct horse battery staple")


def test_roles_grant_only_explicit_capabilities():
    reviewer = PortalUser(
        username="reviewer.one",
        display_name="Reviewer One",
        roles=["reviewer"],
        password_hash="unused",
    )
    identity = SessionIdentity(
        username=reviewer.username,
        display_name=reviewer.display_name,
        roles=reviewer.roles,
        csrf_token="csrf",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    require_capability(identity, "read")
    require_capability(identity, "review")
    with pytest.raises(ValueError, match="not authorized"):
        require_capability(identity, "manage")
