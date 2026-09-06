"""Local portal identities and signed, revocable session cookies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from specvora.portal_session_store import (
    HttpPortalSessionStore,
    PortalSessionState,
    PortalSessionStore,
)

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
    totp_secret: str | None = Field(default=None, min_length=32, max_length=128)
    last_totp_counter: int | None = Field(default=None, ge=0)


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


def authenticate(
    username: str,
    password: str,
    totp_code: str | None = None,
    *,
    now: datetime | None = None,
) -> PortalUser:
    users = _load_users()
    user = next((item for item in users.users if item.username == username), None)
    if user is None or not user.active or not verify_password(password, user.password_hash):
        raise ValueError("Invalid portal credentials")
    if user.totp_secret:
        counter = verify_totp(user.totp_secret, totp_code or "", now=now)
        if counter is None:
            raise ValueError("Invalid portal credentials")
        store = _state_store()
        if store:
            if not store.claim_mfa_counter(user.username, counter):
                raise ValueError("Invalid portal credentials")
        else:
            if user.last_totp_counter is not None and counter <= user.last_totp_counter:
                raise ValueError("Invalid portal credentials")
            user.last_totp_counter = counter
            _write_users(_users_path(), users)
    return user


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def totp_code(secret: str, *, now: datetime | None = None, digits: int = 6) -> str:
    instant = now or datetime.now(UTC)
    counter = int(instant.timestamp()) // 30
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.digest(key, struct.pack(">Q", counter), "sha1")
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10**digits)).zfill(digits)


def verify_totp(secret: str, code: str, *, now: datetime | None = None) -> int | None:
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    instant = now or datetime.now(UTC)
    current = int(instant.timestamp()) // 30
    for counter in range(current - 1, current + 2):
        candidate_time = datetime.fromtimestamp(counter * 30, UTC)
        if hmac.compare_digest(totp_code(secret, now=candidate_time), code):
            return counter
    return None


def issue_session(user: PortalUser, *, now: datetime | None = None) -> tuple[str, SessionIdentity]:
    issued = now or datetime.now(UTC)
    expires = issued + timedelta(minutes=_session_minutes())
    csrf = secrets.token_urlsafe(24)
    session_id = secrets.token_urlsafe(24)
    payload = {
        "version": "specvora-session-v1",
        "username": user.username,
        "session_version": user.session_version,
        "csrf": csrf,
        "session_id": session_id,
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
    if store := _state_store():
        store.register_session(session_id, user.username, expires)
    return f"{encoded}.{signature}", identity


def verify_session(token: str, *, now: datetime | None = None) -> SessionIdentity:
    try:
        encoded, supplied = token.split(".", 1)
        expected = _encode(hmac.digest(_session_key(), encoded.encode("ascii"), "sha256"))
        if not hmac.compare_digest(supplied, expected):
            raise ValueError
        payload = json.loads(_decode(encoded))
        expires = datetime.fromisoformat(payload["expires_at"])
        instant = now or datetime.now(UTC)
        if payload["version"] != "specvora-session-v1" or instant >= expires:
            raise ValueError
        if (store := _state_store()) and not store.session_is_active(
            payload["session_id"], instant
        ):
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


def revoke_portal_session(token: str) -> None:
    if not (store := _state_store()):
        return
    try:
        encoded, _signature = token.split(".", 1)
        session_id = json.loads(_decode(encoded))["session_id"]
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Portal session is invalid or expired") from exc
    store.revoke_session(session_id)


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
    _write_users(users_file, store)
    return user


def enable_portal_mfa(users_file: Path, username: str) -> tuple[PortalUser, str]:
    store = PortalUsers.model_validate_json(users_file.read_bytes())
    user = next((item for item in store.users if item.username == username), None)
    if user is None:
        raise ValueError("Portal user does not exist")
    if user.totp_secret:
        raise ValueError("Portal MFA is already enabled")
    user.totp_secret = generate_totp_secret()
    user.last_totp_counter = None
    user.session_version += 1
    _write_users(users_file, store)
    label = f"Specvora:{username}"
    uri = f"otpauth://totp/{label}?secret={user.totp_secret}&issuer=Specvora&digits=6&period=30"
    return user, uri


def _write_users(users_file: Path, store: PortalUsers) -> None:
    users_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = users_file.with_name(f".{users_file.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(store.model_dump_json(indent=2) + "\n")
        temporary.replace(users_file)
    finally:
        temporary.unlink(missing_ok=True)


def _load_users() -> PortalUsers:
    return PortalUsers.model_validate_json(_users_path().read_bytes())


def _users_path() -> Path:
    path = os.getenv("SPECVORA_PORTAL_USERS_FILE")
    if not path:
        raise ValueError("Portal user configuration is missing")
    return Path(path)


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


def _state_store() -> PortalSessionState | None:
    backend = os.getenv("SPECVORA_PORTAL_STATE_BACKEND")
    path = os.getenv("SPECVORA_PORTAL_STATE_DB")
    if backend is None and path:
        backend = "sqlite"
    if backend is None:
        return None
    if backend == "http":
        endpoint = os.getenv("SPECVORA_PORTAL_STATE_ENDPOINT", "")
        token = os.getenv("SPECVORA_PORTAL_STATE_TOKEN", "")
        return HttpPortalSessionStore(endpoint, token)
    if backend != "sqlite":
        raise ValueError("Unsupported portal state backend")
    if not path:
        raise ValueError("SQLite portal state path is missing")
    return PortalSessionStore(Path(path))


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
