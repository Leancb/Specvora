"""Read-only deterministic monitoring for governed OIDC trust."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from specvora.oidc import JwkSet, validate_jwk_set
from specvora.oidc_trust import discover_oidc_trust
from specvora.oidc_trust_approval import verify_oidc_trust_audit


class OidcTrustMonitorReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["specvora-oidc-monitor-v1"] = "specvora-oidc-monitor-v1"
    status: Literal["HEALTHY", "REVIEW_REQUIRED", "BLOCKED"]
    issuer: str
    current_jwks_sha256: str | None
    discovered_jwks_sha256: str | None
    current_key_ids: list[str]
    discovered_key_ids: list[str]
    findings: list[Literal[
        "TRUST_FILE_INVALID", "AUDIT_INVALID", "TRUST_AUDIT_MISMATCH",
        "DISCOVERY_UNAVAILABLE", "PROVIDER_KEYS_CHANGED", "TRUST_DISCONTINUITY",
    ]]
    checked_at: datetime


def monitor_oidc_trust(
    discovery_endpoint: str,
    issuer: str,
    allowed_hosts: set[str],
    trust_file: Path,
    audit_log: Path,
    workspace_root: Path,
    *,
    now: datetime | None = None,
    transport=None,
) -> OidcTrustMonitorReport:
    instant = now or datetime.now(UTC)
    trust_path = _confined(trust_file, workspace_root, ".json")
    audit_path = _confined(audit_log, workspace_root, ".jsonl")
    try:
        current = validate_jwk_set(trust_path.read_bytes())
        current_hash = _jwks_hash(current)
    except (OSError, ValueError):
        return _report("BLOCKED", issuer, None, None, [], [], ["TRUST_FILE_INVALID"], instant)
    current_ids = sorted(key["kid"] for key in current.keys)
    if not audit_path.is_file() or not audit_path.stat().st_size or not verify_oidc_trust_audit(
        audit_path
    ):
        return _report(
            "BLOCKED", issuer, current_hash, None, current_ids, [], ["AUDIT_INVALID"], instant
        )
    try:
        last = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[-1])
        if last["change"]["new_jwks_sha256"] != current_hash:
            return _report(
                "BLOCKED", issuer, current_hash, None, current_ids, [],
                ["TRUST_AUDIT_MISMATCH"], instant,
            )
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return _report(
            "BLOCKED", issuer, current_hash, None, current_ids, [], ["AUDIT_INVALID"], instant
        )
    try:
        _metadata, discovered = discover_oidc_trust(
            discovery_endpoint, issuer, allowed_hosts, transport=transport
        )
    except (OSError, ValueError):
        return _report(
            "BLOCKED", issuer, current_hash, None, current_ids, [],
            ["DISCOVERY_UNAVAILABLE"], instant,
        )
    discovered_hash = _jwks_hash(discovered)
    discovered_ids = sorted(key["kid"] for key in discovered.keys)
    if discovered_hash == current_hash:
        return _report(
            "HEALTHY", issuer, current_hash, discovered_hash,
            current_ids, discovered_ids, [], instant,
        )
    if set(current_ids) & set(discovered_ids):
        return _report(
            "REVIEW_REQUIRED", issuer, current_hash, discovered_hash,
            current_ids, discovered_ids, ["PROVIDER_KEYS_CHANGED"], instant,
        )
    return _report(
        "BLOCKED", issuer, current_hash, discovered_hash, current_ids, discovered_ids,
        ["TRUST_DISCONTINUITY"], instant,
    )


def _jwks_hash(jwks: JwkSet) -> str:
    canonical = json.dumps(jwks.model_dump(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _report(status, issuer, current_hash, discovered_hash, current_ids, discovered_ids,
            findings, instant) -> OidcTrustMonitorReport:
    return OidcTrustMonitorReport(
        status=status, issuer=issuer, current_jwks_sha256=current_hash,
        discovered_jwks_sha256=discovered_hash, current_key_ids=current_ids,
        discovered_key_ids=discovered_ids, findings=findings, checked_at=instant,
    )


def _confined(path: Path, root: Path, suffix: str) -> Path:
    resolved = (path if path.is_absolute() else root / path).resolve()
    if resolved.suffix.lower() != suffix or not resolved.is_relative_to(root.resolve()):
        raise ValueError("OIDC monitoring artifact escapes the workspace")
    return resolved
