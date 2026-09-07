"""Strict offline validation boundary for OIDC ID tokens."""

from __future__ import annotations

import base64
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class OidcHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alg: str
    kid: str = Field(pattern=r"^[A-Za-z0-9._-]{1,128}$")
    typ: str | None = None


class OidcClaims(BaseModel):
    model_config = ConfigDict(extra="ignore")
    iss: str
    aud: str | list[str]
    sub: str = Field(min_length=1, max_length=255)
    exp: int
    iat: int
    nbf: int | None = None
    nonce: str = Field(min_length=16, max_length=256)
    preferred_username: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,63}$")
    azp: str | None = None


class JwkSet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keys: list[dict] = Field(min_length=1, max_length=20)


def verify_oidc_id_token(
    token: str, expected_nonce: str, *, now: datetime | None = None
) -> OidcClaims:
    try:
        if len(token) > 16_384 or len(expected_nonce) < 16:
            raise ValueError
        encoded_header, encoded_claims, encoded_signature = token.split(".")
        header = OidcHeader.model_validate_json(_decode(encoded_header))
        if header.alg != "RS256" or header.typ not in {None, "JWT"}:
            raise ValueError
        issuer = os.getenv("SPECVORA_OIDC_ISSUER", "")
        audience = os.getenv("SPECVORA_OIDC_AUDIENCE", "")
        parsed = urlparse(issuer)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError
        key = _public_key(header.kid)
        key.verify(
            _decode(encoded_signature),
            f"{encoded_header}.{encoded_claims}".encode("ascii"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        claims = OidcClaims.model_validate_json(_decode(encoded_claims))
        instant = int((now or datetime.now(UTC)).timestamp())
        audiences = [claims.aud] if isinstance(claims.aud, str) else claims.aud
        if (
            claims.iss != issuer
            or not audience
            or audience not in audiences
            or (len(audiences) > 1 and claims.azp != audience)
            or claims.nonce != expected_nonce
            or claims.exp <= instant - 60
            or claims.iat > instant + 60
            or (claims.nbf is not None and claims.nbf > instant + 60)
        ):
            raise ValueError
        return claims
    except (
        InvalidSignature, KeyError, OSError, ValueError, TypeError,
        ValidationError, json.JSONDecodeError,
    ) as exc:
        raise ValueError("OIDC identity token is invalid") from exc


def _public_key(kid: str) -> rsa.RSAPublicKey:
    path = os.getenv("SPECVORA_OIDC_JWKS_FILE", "")
    raw = Path(path).read_bytes()
    if len(raw) > 65_536:
        raise ValueError
    jwks = JwkSet.model_validate_json(raw)
    matches = [key for key in jwks.keys if key.get("kid") == kid]
    if len(matches) != 1:
        raise ValueError
    key = matches[0]
    if set(key) - {"kty", "kid", "use", "alg", "n", "e"}:
        raise ValueError
    if key.get("kty") != "RSA" or key.get("use") not in {None, "sig"}:
        raise ValueError
    if key.get("alg") not in {None, "RS256"}:
        raise ValueError
    modulus = int.from_bytes(_decode(key["n"]), "big")
    exponent = int.from_bytes(_decode(key["e"]), "big")
    public = rsa.RSAPublicNumbers(exponent, modulus).public_key()
    if public.key_size < 2048 or exponent != 65_537:
        raise ValueError
    return public


def _decode(value: str) -> bytes:
    if not value or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
