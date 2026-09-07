import base64
import json
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from specvora.oidc import verify_oidc_id_token
from specvora.portal_auth import authenticate_oidc, hash_password


def encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def configured_oidc(tmp_path, monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private.public_key().public_numbers()
    jwks = {
        "keys": [{
            "kty": "RSA", "kid": "key-1", "use": "sig", "alg": "RS256",
            "n": encode(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")),
            "e": encode(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")),
        }]
    }
    target = tmp_path / "jwks.json"
    target.write_text(json.dumps(jwks), encoding="utf-8")
    monkeypatch.setenv("SPECVORA_OIDC_ISSUER", "https://identity.example/tenant")
    monkeypatch.setenv("SPECVORA_OIDC_AUDIENCE", "specvora-portal")
    monkeypatch.setenv("SPECVORA_OIDC_JWKS_FILE", str(target))
    return private


def token(private, claims, *, header=None):
    actual_header = header or {"alg": "RS256", "kid": "key-1", "typ": "JWT"}
    parts = [encode(json.dumps(actual_header, separators=(",", ":")).encode()),
             encode(json.dumps(claims, separators=(",", ":")).encode())]
    signing_input = ".".join(parts).encode()
    signature = private.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return ".".join([*parts, encode(signature)])


def claims(now):
    instant = int(now.timestamp())
    return {
        "iss": "https://identity.example/tenant", "aud": "specvora-portal",
        "sub": "provider-subject", "preferred_username": "reviewer.one",
        "nonce": "expected-nonce-value", "iat": instant, "exp": instant + 300,
        "roles": ["operator"],
    }


def test_oidc_verifies_signature_identity_and_expected_nonce(tmp_path, monkeypatch):
    private = configured_oidc(tmp_path, monkeypatch)
    now = datetime(2026, 9, 7, tzinfo=UTC)
    result = verify_oidc_id_token(token(private, claims(now)), "expected-nonce-value", now=now)
    assert result.preferred_username == "reviewer.one"
    assert not hasattr(result, "roles")


@pytest.mark.parametrize("change", ["issuer", "audience", "nonce", "expired", "future"])
def test_oidc_rejects_invalid_registered_claims(tmp_path, monkeypatch, change):
    private = configured_oidc(tmp_path, monkeypatch)
    now = datetime(2026, 9, 7, tzinfo=UTC)
    payload = claims(now)
    if change == "issuer":
        payload["iss"] = "https://attacker.example"
    elif change == "audience":
        payload["aud"] = "other-client"
    elif change == "nonce":
        payload["nonce"] = "different-nonce-value"
    elif change == "expired":
        payload["exp"] = int(now.timestamp()) - 61
    else:
        payload["iat"] = int(now.timestamp()) + 61
    with pytest.raises(ValueError, match="identity token is invalid"):
        verify_oidc_id_token(token(private, payload), "expected-nonce-value", now=now)


def test_oidc_rejects_algorithm_key_and_signature_confusion(tmp_path, monkeypatch):
    private = configured_oidc(tmp_path, monkeypatch)
    now = datetime(2026, 9, 7, tzinfo=UTC)
    with pytest.raises(ValueError, match="identity token is invalid"):
        verify_oidc_id_token(token(private, claims(now), header={"alg": "none", "kid": "key-1"}),
                             "expected-nonce-value", now=now)
    unknown = token(private, claims(now), header={"alg": "RS256", "kid": "unknown"})
    with pytest.raises(ValueError, match="identity token is invalid"):
        verify_oidc_id_token(unknown, "expected-nonce-value", now=now)
    valid = token(private, claims(now))
    head, signature = valid.rsplit(".", 1)
    tampered = head + "." + ("A" if signature[0] != "A" else "B") + signature[1:]
    with pytest.raises(ValueError, match="identity token is invalid"):
        verify_oidc_id_token(tampered, "expected-nonce-value", now=now)


def test_oidc_maps_only_to_preconfigured_local_roles(tmp_path, monkeypatch):
    private = configured_oidc(tmp_path, monkeypatch)
    users = tmp_path / "users.json"
    users.write_text(json.dumps({"users": [{
        "username": "reviewer.one", "display_name": "Reviewer One", "roles": ["reviewer"],
        "password_hash": hash_password("unused-local-password"),
    }]}), encoding="utf-8")
    monkeypatch.setenv("SPECVORA_PORTAL_USERS_FILE", str(users))
    monkeypatch.setenv("SPECVORA_PORTAL_STATE_BACKEND", "sqlite")
    monkeypatch.setenv("SPECVORA_PORTAL_STATE_DB", str(tmp_path / "state.db"))
    now = datetime(2026, 9, 7, tzinfo=UTC)
    user = authenticate_oidc(token(private, claims(now)), "expected-nonce-value", now=now)
    assert user.roles == ["reviewer"]
