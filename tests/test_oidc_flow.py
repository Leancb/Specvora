import base64
import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from specvora.oidc_flow import begin_oidc_login, complete_oidc_login
from specvora.portal_session_store import PortalSessionStore


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def configure_identity(tmp_path, monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = key.public_key().public_numbers()
    jwks = {"keys": [{
        "kty": "RSA", "kid": "key-1", "use": "sig", "alg": "RS256",
        "n": b64(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")),
        "e": b64(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")),
    }]}
    path = tmp_path / "jwks.json"
    path.write_text(json.dumps(jwks), encoding="utf-8")
    monkeypatch.setenv("SPECVORA_OIDC_JWKS_FILE", str(path))
    monkeypatch.setenv("SPECVORA_OIDC_ISSUER", "https://identity.example/tenant")
    monkeypatch.setenv("SPECVORA_OIDC_AUDIENCE", "specvora")
    return key


def id_token(key, nonce, now):
    header = b64(json.dumps({"alg": "RS256", "kid": "key-1", "typ": "JWT"}).encode())
    claims = b64(json.dumps({
        "iss": "https://identity.example/tenant", "aud": "specvora", "sub": "subject-1",
        "exp": int((now + timedelta(minutes=5)).timestamp()), "iat": int(now.timestamp()),
        "nonce": nonce, "preferred_username": "user.one",
    }).encode())
    signing_input = f"{header}.{claims}".encode()
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{claims}.{b64(signature)}"


def test_authorization_request_uses_pkce_and_stores_only_state_digest(tmp_path):
    path = tmp_path / "state.db"
    store = PortalSessionStore(path)
    url = begin_oidc_login(
        store, "https://identity.example/authorize", "specvora",
        "http://127.0.0.1:8102/api/session/oidc/callback",
        now=datetime(2026, 9, 7, tzinfo=UTC),
    )
    query = parse_qs(urlparse(url).query)
    assert query["code_challenge_method"] == ["S256"]
    assert query["response_type"] == ["code"]
    with sqlite3.connect(path) as connection:
        digest, nonce, verifier = connection.execute(
            "SELECT state_digest, nonce, code_verifier FROM oidc_transactions"
        ).fetchone()
    assert digest == hashlib.sha256(query["state"][0].encode()).hexdigest()
    assert query["state"][0] not in {digest, nonce, verifier}
    assert query["nonce"] == [nonce]
    assert query["code_challenge"] == [b64(hashlib.sha256(verifier.encode()).digest())]


def test_code_exchange_claims_transaction_before_validating_token(tmp_path, monkeypatch):
    now = datetime(2026, 9, 7, tzinfo=UTC)
    key = configure_identity(tmp_path, monkeypatch)
    store = PortalSessionStore(tmp_path / "state.db")
    url = begin_oidc_login(store, "https://identity.example/authorize", "specvora",
                           "http://127.0.0.1:8102/callback", now=now)
    state = parse_qs(urlparse(url).query)["state"][0]
    calls = []

    def handler(request):
        calls.append(request)
        with sqlite3.connect(tmp_path / "state.db") as connection:
            assert connection.execute("SELECT COUNT(*) FROM oidc_transactions").fetchone()[0] == 0
        return httpx.Response(200, json={"id_token": id_token(key, form_nonce, now)})

    with sqlite3.connect(tmp_path / "state.db") as connection:
        form_nonce = connection.execute("SELECT nonce FROM oidc_transactions").fetchone()[0]
    claims = complete_oidc_login(
        store, state, "authorization-code", "https://identity.example/token", "specvora",
        "http://127.0.0.1:8102/callback", {"identity.example"}, now=now,
        transport=httpx.MockTransport(handler),
    )
    assert claims.preferred_username == "user.one"
    form = parse_qs(calls[0].content.decode())
    assert form["grant_type"] == ["authorization_code"]
    assert len(form["code_verifier"][0]) >= 43
    with pytest.raises(ValueError, match="transaction"):
        complete_oidc_login(
            store, state, "authorization-code", "https://identity.example/token", "specvora",
            "http://127.0.0.1:8102/callback", {"identity.example"}, now=now,
            transport=httpx.MockTransport(handler),
        )
    assert len(calls) == 1


def test_token_exchange_rejects_unallowlisted_destination(tmp_path):
    store = PortalSessionStore(tmp_path / "state.db")
    with pytest.raises(ValueError, match="not allowed"):
        complete_oidc_login(
            store, "s" * 32, "code-value", "https://evil.example/token", "specvora",
            "https://app.example/callback", {"identity.example"},
        )
