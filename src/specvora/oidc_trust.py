"""Pinned OIDC discovery and atomic JWKS rotation."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict

from specvora.oidc import validate_jwk_set


class ProviderMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    response_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]
    code_challenge_methods_supported: list[str]


def refresh_oidc_trust(
    discovery_endpoint: str,
    expected_issuer: str,
    allowed_hosts: set[str],
    output_file: Path,
    workspace_root: Path,
    *,
    bootstrap: bool = False,
    transport=None,
) -> dict[str, object]:
    normalized_hosts = {host.casefold().rstrip(".") for host in allowed_hosts}
    discovery = _allowed_endpoint(discovery_endpoint, normalized_hosts)
    if not discovery.path.endswith("/.well-known/openid-configuration"):
        raise ValueError("OIDC discovery endpoint is invalid")
    issuer = _allowed_endpoint(expected_issuer, normalized_hosts)
    target = (output_file if output_file.is_absolute() else workspace_root / output_file).resolve()
    if target.suffix.lower() != ".json" or not target.is_relative_to(workspace_root.resolve()):
        raise ValueError("OIDC trust file escapes the workspace")
    if target.exists() == bootstrap:
        action = "requires an absent file" if bootstrap else "requires an existing file"
        raise ValueError(f"OIDC trust operation {action}")

    _metadata, new_set = discover_oidc_trust(
        discovery_endpoint, expected_issuer, normalized_hosts, transport=transport
    )
    new_kids = {key["kid"] for key in new_set.keys}
    if not bootstrap:
        current = validate_jwk_set(target.read_bytes())
        current_kids = {key["kid"] for key in current.keys}
        if not current_kids & new_kids:
            raise ValueError("OIDC JWKS rotation has no trusted overlap")
    canonical = json.dumps(
        new_set.model_dump(), sort_keys=True, separators=(",", ":")
    ).encode() + b"\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(canonical)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "status": "BOOTSTRAPPED" if bootstrap else "ROTATED",
        "issuer": issuer.geturl(), "key_ids": sorted(new_kids), "output": str(target),
    }


def discover_oidc_trust(
    discovery_endpoint: str,
    expected_issuer: str,
    allowed_hosts: set[str],
    *,
    transport=None,
):
    normalized_hosts = {host.casefold().rstrip(".") for host in allowed_hosts}
    discovery = _allowed_endpoint(discovery_endpoint, normalized_hosts)
    if not discovery.path.endswith("/.well-known/openid-configuration"):
        raise ValueError("OIDC discovery endpoint is invalid")
    _allowed_endpoint(expected_issuer, normalized_hosts)
    try:
        with httpx.Client(
            timeout=5, follow_redirects=False, trust_env=False, transport=transport,
            headers={"Accept": "application/json"},
        ) as client:
            metadata = ProviderMetadata.model_validate_json(_response_bytes(
                client.get(discovery_endpoint), "discovery"
            ))
            if metadata.issuer != expected_issuer:
                raise ValueError("OIDC discovered issuer differs from the pinned issuer")
            if (
                "code" not in metadata.response_types_supported
                or "RS256" not in metadata.id_token_signing_alg_values_supported
                or "S256" not in metadata.code_challenge_methods_supported
            ):
                raise ValueError("OIDC provider lacks required secure capabilities")
            for endpoint in (
                metadata.authorization_endpoint, metadata.token_endpoint, metadata.jwks_uri
            ):
                _allowed_endpoint(endpoint, normalized_hosts)
            raw_jwks = _response_bytes(client.get(metadata.jwks_uri), "JWKS")
    except httpx.HTTPError as exc:
        raise ValueError("OIDC trust endpoint is unavailable") from exc
    return metadata, validate_jwk_set(raw_jwks)


def _allowed_endpoint(value: str, allowed_hosts: set[str]):
    parsed = urlparse(value)
    host = parsed.hostname.casefold().rstrip(".") if parsed.hostname else ""
    if (
        parsed.scheme != "https" or not host or host not in allowed_hosts
        or parsed.username or parsed.password or parsed.query or parsed.fragment
    ):
        raise ValueError("OIDC endpoint is not an allowed HTTPS destination")
    return parsed


def _response_bytes(response: httpx.Response, label: str) -> bytes:
    if response.status_code != 200 or not response.content or len(response.content) > 65_536:
        raise ValueError(f"OIDC {label} response is invalid")
    return response.content
