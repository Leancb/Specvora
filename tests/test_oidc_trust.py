import base64
import json

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from specvora.oidc_trust import refresh_oidc_trust


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def jwk(kid: str) -> dict:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    numbers = key.public_numbers()
    return {
        "kty": "RSA", "kid": kid, "use": "sig", "alg": "RS256",
        "n": b64(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")),
        "e": b64(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")),
    }


def transport_for(keys, *, issuer="https://identity.example/tenant",
                  jwks_uri="https://keys.example/jwks"):
    def handler(request):
        if request.url.path.endswith("openid-configuration"):
            return httpx.Response(200, json={
                "issuer": issuer,
                "authorization_endpoint": "https://identity.example/authorize",
                "token_endpoint": "https://identity.example/token",
                "jwks_uri": jwks_uri,
                "response_types_supported": ["code"],
                "id_token_signing_alg_values_supported": ["RS256"],
                "code_challenge_methods_supported": ["S256"],
                "unrelated_standard_metadata": True,
            })
        return httpx.Response(200, json={"keys": keys})
    return httpx.MockTransport(handler)


def refresh(tmp_path, keys, *, bootstrap, transport=None):
    return refresh_oidc_trust(
        "https://identity.example/tenant/.well-known/openid-configuration",
        "https://identity.example/tenant", {"identity.example", "keys.example"},
        tmp_path / "trust/jwks.json", tmp_path, bootstrap=bootstrap,
        transport=transport or transport_for(keys),
    )


def test_bootstrap_and_overlapping_rotation_are_atomic(tmp_path):
    first = jwk("key-a")
    second = jwk("key-b")
    result = refresh(tmp_path, [first], bootstrap=True)
    assert result["status"] == "BOOTSTRAPPED"
    assert result["key_ids"] == ["key-a"]
    result = refresh(tmp_path, [first, second], bootstrap=False)
    assert result["status"] == "ROTATED"
    assert json.loads((tmp_path / "trust/jwks.json").read_text())["keys"] == [first, second]
    assert not list((tmp_path / "trust").glob("*.tmp"))


def test_rotation_requires_overlap_and_preserves_current_file(tmp_path):
    first = jwk("key-a")
    refresh(tmp_path, [first], bootstrap=True)
    before = (tmp_path / "trust/jwks.json").read_bytes()
    with pytest.raises(ValueError, match="overlap"):
        refresh(tmp_path, [jwk("key-b")], bootstrap=False)
    assert (tmp_path / "trust/jwks.json").read_bytes() == before


@pytest.mark.parametrize(
    ("transport", "message"),
    [
        (transport_for([jwk("key-a")], issuer="https://evil.example"), "pinned issuer"),
        (transport_for([jwk("key-a")], jwks_uri="https://evil.example/jwks"), "allowed HTTPS"),
    ],
)
def test_discovery_rejects_unpinned_metadata(tmp_path, transport, message):
    with pytest.raises(ValueError, match=message):
        refresh(tmp_path, [], bootstrap=True, transport=transport)


def test_trust_file_must_be_confined_and_operations_explicit(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        refresh_oidc_trust(
            "https://identity.example/.well-known/openid-configuration",
            "https://identity.example", {"identity.example"}, tmp_path.parent / "jwks.json",
            tmp_path, bootstrap=True, transport=transport_for([jwk("key-a")]),
        )
    with pytest.raises(ValueError, match="existing"):
        refresh(tmp_path, [jwk("key-a")], bootstrap=False)
