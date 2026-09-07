"""Confined, one-use OIDC Authorization Code + PKCE flow."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urlparse

import httpx

from specvora.oidc import OidcClaims, verify_oidc_id_token
from specvora.portal_session_store import PortalSessionState


def begin_oidc_login(
    state_store: PortalSessionState,
    authorization_endpoint: str,
    client_id: str,
    redirect_uri: str,
    *,
    now: datetime | None = None,
) -> str:
    _safe_endpoint(authorization_endpoint, "authorization")
    _safe_redirect(redirect_uri)
    _safe_client_id(client_id)
    instant = now or datetime.now(UTC)
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    state_store.register_oidc_transaction(
        _digest(state), nonce, verifier, instant + timedelta(minutes=5)
    )
    query = urlencode({
        "response_type": "code", "response_mode": "query", "scope": "openid profile",
        "client_id": client_id, "redirect_uri": redirect_uri, "state": state, "nonce": nonce,
        "code_challenge": _b64(hashlib.sha256(verifier.encode()).digest()),
        "code_challenge_method": "S256",
    })
    return f"{authorization_endpoint}?{query}"


def complete_oidc_login(
    state_store: PortalSessionState,
    state: str,
    code: str,
    token_endpoint: str,
    client_id: str,
    redirect_uri: str,
    allowed_hosts: set[str],
    *,
    now: datetime | None = None,
    transport=None,
) -> OidcClaims:
    _safe_value(state, 32, 256)
    _safe_value(code, 8, 4096)
    parsed = _safe_endpoint(token_endpoint, "token")
    if parsed.hostname not in {host.lower() for host in allowed_hosts}:
        raise ValueError("OIDC token endpoint is not allowed")
    _safe_redirect(redirect_uri)
    _safe_client_id(client_id)
    instant = now or datetime.now(UTC)
    transaction = state_store.claim_oidc_transaction(_digest(state), instant)
    if transaction is None:
        raise ValueError("OIDC transaction is invalid")
    nonce, verifier = transaction
    data = {
        "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri,
        "client_id": client_id, "code_verifier": verifier,
    }
    secret = os.getenv("SPECVORA_OIDC_CLIENT_SECRET")
    if secret:
        _safe_value(secret, 8, 4096)
        data["client_secret"] = secret
    try:
        with httpx.Client(
            timeout=5, follow_redirects=False, trust_env=False, transport=transport
        ) as client:
            response = client.post(token_endpoint, data=data)
        if response.status_code != 200 or len(response.content) > 65_536:
            raise ValueError
        payload = response.json()
        if not isinstance(payload, dict) or set(payload) - {
            "access_token", "token_type", "expires_in", "scope", "id_token"
        }:
            raise ValueError
        token = payload.get("id_token")
        if not isinstance(token, str):
            raise ValueError
        return verify_oidc_id_token(token, nonce, now=instant)
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise ValueError("OIDC authorization response is invalid") from exc


def _safe_endpoint(value: str, label: str):
    parsed = urlparse(value)
    if (
        parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
        or parsed.query or parsed.fragment or not parsed.path
    ):
        raise ValueError(f"OIDC {label} endpoint is unsafe")
    return parsed


def _safe_redirect(value: str) -> None:
    parsed = urlparse(value)
    loopback = parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}
    if (
        not parsed.hostname or parsed.username or parsed.password or parsed.fragment
        or (parsed.scheme != "https" and not loopback)
    ):
        raise ValueError("OIDC redirect URI is unsafe")


def _safe_client_id(value: str) -> None:
    _safe_value(value, 3, 256)


def _safe_value(value: str, minimum: int, maximum: int) -> None:
    if not minimum <= len(value) <= maximum or any(character.isspace() for character in value):
        raise ValueError("OIDC input is invalid")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
