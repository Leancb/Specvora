"""Central portal-state service. Deploy only behind authenticated TLS."""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from specvora.portal_session_store import PortalSessionStore

app = FastAPI(title="Specvora Portal State Service", version="0.1.0", docs_url=None)
_stores: dict[str, PortalSessionStore] = {}
_stores_lock = Lock()


class MfaClaim(BaseModel):
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,63}$")
    counter: int = Field(ge=0)


class OidcTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    nonce: str = Field(pattern=r"^[A-Za-z0-9_-]{32,256}$")
    code_verifier: str = Field(pattern=r"^[A-Za-z0-9._~-]{43,128}$")
    expires_at: datetime


class OidcTransactionClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime


class SessionRegistration(BaseModel):
    session_id: str = Field(min_length=16, max_length=200)
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,63}$")
    expires_at: datetime


class LoginAttempt(BaseModel):
    subject: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime
    limit: int = Field(ge=1, le=20)
    window_seconds: int = Field(ge=60, le=3600)


class RecoveryCodeSet(BaseModel):
    digests: list[str] = Field(min_length=1, max_length=12)


class RecoveryCodeClaim(BaseModel):
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,63}$")
    code_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class SecurityEvent(BaseModel):
    event_type: Literal[
        "login_failed", "login_throttled", "login_succeeded",
        "recovery_used", "recovery_rotated",
    ]
    subject: str = Field(pattern=r"^[0-9a-f]{64}$")
    occurred_at: datetime


class ServiceTokenDigest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    not_before: datetime
    expires_at: datetime


class ServiceTokenTrust(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["specvora-state-service-trust-v1"]
    tokens: list[ServiceTokenDigest] = Field(min_length=1, max_length=8)


def _authorize(authorization: Annotated[str | None, Header()] = None) -> None:
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if (
        not authorization
        or not authorization.startswith("Bearer ")
        or not 32 <= len(supplied) <= 4096
        or any(character.isspace() for character in supplied)
        or not _token_is_trusted(supplied)
    ):
        raise HTTPException(status_code=401, detail="State service authentication failed")


def _token_is_trusted(supplied: str) -> bool:
    trust_path = os.getenv("SPECVORA_STATE_SERVICE_TOKEN_FILE")
    if not trust_path:
        token = os.getenv("SPECVORA_STATE_SERVICE_TOKEN", "")
        return len(token) >= 32 and hmac.compare_digest(supplied, token)
    try:
        raw = Path(trust_path).read_bytes()
        if len(raw) > 65_536:
            return False
        trust = ServiceTokenTrust.model_validate_json(raw)
        now = datetime.now(UTC)
        supplied_digest = hashlib.sha256(supplied.encode("utf-8")).hexdigest()
        active = []
        for token in trust.tokens:
            if token.not_before.tzinfo is None or token.expires_at.tzinfo is None:
                return False
            if token.not_before >= token.expires_at:
                return False
            if token.not_before <= now < token.expires_at:
                active.append(token.token_sha256)
        return any(hmac.compare_digest(supplied_digest, digest) for digest in active)
    except (OSError, ValueError, ValidationError):
        return False


def _store_for_path(path: str) -> PortalSessionStore:
    with _stores_lock:
        store = _stores.get(path)
        if store is None:
            store = PortalSessionStore(Path(path))
            _stores[path] = store
        return store


def _store() -> PortalSessionStore:
    path = os.getenv("SPECVORA_STATE_SERVICE_DB")
    if not path:
        raise HTTPException(status_code=503, detail="State service storage is unavailable")
    return _store_for_path(str(Path(path).resolve()))


Authorized = Annotated[None, Depends(_authorize)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/v1/mfa-claims", status_code=201)
def claim_mfa(claim: MfaClaim, _authorized: Authorized) -> Response:
    if not _store().claim_mfa_counter(claim.username, claim.counter):
        raise HTTPException(status_code=409, detail="MFA counter was already claimed")
    return Response(status_code=201)


@app.post("/v1/oidc-transactions", status_code=201)
def register_oidc_transaction(transaction: OidcTransaction, _authorized: Authorized) -> Response:
    if transaction.expires_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="Timezone-aware timestamp is required")
    try:
        _store().register_oidc_transaction(
            transaction.state_digest, transaction.nonce,
            transaction.code_verifier, transaction.expires_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail="OIDC transaction is unavailable") from exc
    return Response(status_code=201)


@app.post("/v1/oidc-transaction-claims")
def claim_oidc_transaction(
    claim: OidcTransactionClaim, _authorized: Authorized
) -> dict[str, str]:
    if claim.observed_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="Timezone-aware timestamp is required")
    transaction = _store().claim_oidc_transaction(claim.state_digest, claim.observed_at)
    if transaction is None:
        raise HTTPException(status_code=409, detail="OIDC transaction is unavailable")
    return {"nonce": transaction[0], "code_verifier": transaction[1]}


@app.post("/v1/login-attempts", status_code=201)
def claim_login_attempt(attempt: LoginAttempt, _authorized: Authorized) -> Response:
    if attempt.observed_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="Timezone-aware timestamp is required")
    if not _store().claim_login_attempt(
        attempt.subject, attempt.observed_at, attempt.limit, attempt.window_seconds
    ):
        raise HTTPException(status_code=429, detail="Login attempt limit reached")
    return Response(status_code=201)


@app.delete("/v1/login-attempts/{subject}", status_code=204)
def clear_login_attempts(subject: str, _authorized: Authorized) -> Response:
    if len(subject) != 64 or any(character not in "0123456789abcdef" for character in subject):
        raise HTTPException(status_code=422, detail="Login subject is invalid")
    _store().clear_login_attempts(subject)
    return Response(status_code=204)


@app.put("/v1/recovery-codes/{username}", status_code=204)
def replace_recovery_codes(
    username: str, recovery: RecoveryCodeSet, _authorized: Authorized
) -> Response:
    if (
        len(username) < 3
        or len(username) > 64
        or username[0] not in "abcdefghijklmnopqrstuvwxyz0123456789"
        or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789._-" for character in username)
        or any(len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)
               for digest in recovery.digests)
        or len(set(recovery.digests)) != len(recovery.digests)
    ):
        raise HTTPException(status_code=422, detail="Recovery-code set is invalid")
    _store().replace_recovery_codes(username, recovery.digests)
    return Response(status_code=204)


@app.post("/v1/recovery-code-claims", status_code=201)
def claim_recovery_code(claim: RecoveryCodeClaim, _authorized: Authorized) -> Response:
    if not _store().claim_recovery_code(claim.username, claim.code_digest):
        raise HTTPException(status_code=409, detail="Recovery code is unavailable")
    return Response(status_code=201)


@app.post("/v1/security-events", status_code=201)
def record_security_event(event: SecurityEvent, _authorized: Authorized) -> Response:
    if event.occurred_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="Timezone-aware timestamp is required")
    _store().record_security_event(event.event_type, event.subject, event.occurred_at)
    return Response(status_code=201)


@app.post("/v1/sessions", status_code=201)
def register_session(session: SessionRegistration, _authorized: Authorized) -> Response:
    _store().register_session(session.session_id, session.username, session.expires_at)
    return Response(status_code=201)


@app.get("/v1/sessions/{session_id}")
def session_status(session_id: str, at: datetime, _authorized: Authorized) -> dict[str, bool]:
    return {"active": _store().session_is_active(session_id, at)}


@app.delete("/v1/sessions/{session_id}", status_code=204)
def revoke_session(session_id: str, _authorized: Authorized) -> Response:
    _store().revoke_session(session_id)
    return Response(status_code=204)
