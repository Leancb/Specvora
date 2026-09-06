import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from specvora.portal_auth import (
    PortalUser,
    SessionIdentity,
    add_portal_user,
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


def test_add_portal_user_writes_only_hash_and_rejects_duplicate(tmp_path):
    target = tmp_path / "auth/users.json"
    user = add_portal_user(
        target,
        "operator.one",
        "Operator One",
        ["operator", "reviewer"],
        "operator-password-long",
    )
    assert user.roles == ["operator", "reviewer"]
    content = target.read_text(encoding="utf-8")
    assert "operator-password-long" not in content
    assert "pbkdf2-sha256$600000$" in content
    with pytest.raises(ValueError, match="already exists"):
        add_portal_user(
            target, "operator.one", "Operator One", ["operator"], "another-password-long"
        )


def test_create_portal_user_cli_prompts_without_password_argument(
    tmp_path, monkeypatch, capsys
):
    from specvora.governance_cli import main

    target = tmp_path / "auth/users.json"
    prompts = iter(["operator-password-long", "operator-password-long"])
    monkeypatch.setattr("getpass.getpass", lambda _prompt: next(prompts))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "specvora-governance",
            "--workspace-root",
            str(tmp_path),
            "create-portal-user",
            "--users-file",
            str(target),
            "--username",
            "operator.one",
            "--display-name",
            "Operator One",
            "--role",
            "operator",
            "--role",
            "reviewer",
        ],
    )
    main()
    result = json.loads(capsys.readouterr().out)
    assert result["roles"] == ["operator", "reviewer"]
    assert target.is_file()


def test_setup_script_uses_windows_powershell_compatible_random_generator():
    script = Path("scripts/setup-portal-auth.ps1").read_text(encoding="utf-8")
    assert "RandomNumberGenerator]::Create()" in script
    assert "$generator.GetBytes($bytes)" in script
    assert "RandomNumberGenerator]::Fill" not in script
