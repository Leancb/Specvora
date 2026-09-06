"""Local portal identities and signed, revocable session cookies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PASSWORD_ITERATIONS = 600_000
Role = Literal["viewer", "reviewer", "operator"]
Capability = Literal["read", "review", "manage"]
ROLE_CAPABILITIES: dict[str, set[str]] = {
    "viewer": {"read"},
    "reviewer": {"read", "review"},
    "operator": {"read", "manage"},
}


class PortalUser(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,63}$")
    display_name: str = Field(min_length=3, max_length=120)
    roles: list[Role] = Field(min_length=1)
    password_hash: str
    active: bool = True
    session_version: int = Field(default=1, ge=1)


class PortalUsers(BaseModel):
    model_config = ConfigDict(extra="forbid")
    users: list[PortalUser]


class SessionIdentity(BaseModel):
    username: str
    display_name: str
    roles: list[Role]
    csrf_token: str
    expires_at: datetime


def portal_auth_mode() -> str:
    mode = os.getenv("SPECVORA_PORTAL_AUTH_MODE", "local-development")
    if mode not in {"required", "local-development"}:
        raise ValueError("Invalid portal authentication mode")
    return mode


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if len(password) < 12 or len(password) > 1024:
        raise ValueError("Password must contain between 12 and 1024 characters")
    actual_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), actual_salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2-sha256${PASSWORD_ITERATIONS}${_encode(actual_salt)}${_encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2-sha256" or int(iterations) < PASSWORD_ITERATIONS:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), _decode(salt), int(iterations)
        )
        return hmac.compare_digest(actual, _decode(expected))
    except (ValueError, TypeError):
        return False


def authenticate(username: str, password: str) -> PortalUser:
    users = _load_users()
    user = next((item for item in users.users if item.username == username), None)
    if user is None or not user.active or not verify_password(password, user.password_hash):
        raise ValueError("Invalid portal credentials")
    return user


def issue_session(user: PortalUser, *, now: datetime | None = None) -> tuple[str, SessionIdentity]:
    issued = now or datetime.now(UTC)
    expires = issued + timedelta(minutes=_session_minutes())
    csrf = secrets.token_urlsafe(24)
    payload = {
        "version": "specvora-session-v1",
        "username": user.username,
        "session_version": user.session_version,
        "csrf": csrf,
        "issued_at": issued.isoformat(),
        "expires_at": expires.isoformat(),
    }
    encoded = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    signature = _encode(hmac.digest(_session_key(), encoded.encode("ascii"), "sha256"))
    identity = SessionIdentity(
        username=user.username,
        display_name=user.display_name,
        roles=user.roles,
        csrf_token=csrf,
        expires_at=expires,
    )
    return f"{encoded}.{signature}", identity


def verify_session(token: str, *, now: datetime | None = None) -> SessionIdentity:
    try:
        encoded, supplied = token.split(".", 1)
        expected = _encode(hmac.digest(_session_key(), encoded.encode("ascii"), "sha256"))
        if not hmac.compare_digest(supplied, expected):
            raise ValueError
        payload = json.loads(_decode(encoded))
        expires = datetime.fromisoformat(payload["expires_at"])
        if payload["version"] != "specvora-session-v1" or (now or datetime.now(UTC)) >= expires:
            raise ValueError
        user = next(
            item for item in _load_users().users if item.username == payload["username"]
        )
        if not user.active or user.session_version != payload["session_version"]:
            raise ValueError
        return SessionIdentity(
            username=user.username,
            display_name=user.display_name,
            roles=user.roles,
            csrf_token=payload["csrf"],
            expires_at=expires,
        )
    except (ValueError, KeyError, TypeError, StopIteration, json.JSONDecodeError) as exc:
        raise ValueError("Portal session is invalid or expired") from exc


def require_capability(identity: SessionIdentity, capability: Capability) -> None:
    granted = set().union(*(ROLE_CAPABILITIES[role] for role in identity.roles))
    if capability not in granted:
        raise ValueError("Portal role is not authorized for this action")


def add_portal_user(
    users_file: Path,
    username: str,
    display_name: str,
    roles: list[Role],
    password: str,
) -> PortalUser:
    user = PortalUser(
        username=username,
        display_name=display_name,
        roles=roles,
        password_hash=hash_password(password),
    )
    if users_file.exists():
        store = PortalUsers.model_validate_json(users_file.read_bytes())
    else:
        store = PortalUsers(users=[])
    if any(existing.username == username for existing in store.users):
        raise ValueError("Portal user already exists")
    store.users.append(user)
    users_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = users_file.with_name(f".{users_file.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(store.model_dump_json(indent=2) + "\n")
        temporary.replace(users_file)
    finally:
        temporary.unlink(missing_ok=True)
    return user


def _load_users() -> PortalUsers:
    path = os.getenv("SPECVORA_PORTAL_USERS_FILE")
    if not path:
        raise ValueError("Portal user configuration is missing")
    return PortalUsers.model_validate_json(Path(path).read_bytes())


def _session_key() -> bytes:
    path = os.getenv("SPECVORA_PORTAL_SESSION_KEY")
    if not path:
        raise ValueError("Portal session key configuration is missing")
    key = Path(path).read_bytes()
    if len(key) != 32:
        raise ValueError("Portal session key must contain exactly 32 random bytes")
    return key


def _session_minutes() -> int:
    try:
        minutes = int(os.getenv("SPECVORA_PORTAL_SESSION_MINUTES", "30"))
    except ValueError as exc:
        raise ValueError("Portal session duration is invalid") from exc
    if not 5 <= minutes <= 480:
        raise ValueError("Portal session duration must be between 5 and 480 minutes")
    return minutes


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
