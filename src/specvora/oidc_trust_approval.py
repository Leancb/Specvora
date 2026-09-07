"""Independent signed approval and audit trail for OIDC trust changes."""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from specvora.audit import GENESIS_HASH
from specvora.oidc import JwkSet, validate_jwk_set
from specvora.oidc_trust import discover_oidc_trust
from specvora.signed_approval import SignedApproval, consume_approval


class OidcTrustProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["specvora-oidc-trust-proposal-v1"] = "specvora-oidc-trust-proposal-v1"
    project_id: str = Field(min_length=1, max_length=128)
    issuer: str
    discovery_endpoint: str
    bootstrap: bool
    trust_file: str = Field(min_length=1, max_length=500)
    key_ids: list[str] = Field(min_length=1, max_length=20)
    jwks_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    jwks: JwkSet
    proposed_at: AwareDatetime


def propose_oidc_trust_change(
    project_id: str,
    discovery_endpoint: str,
    issuer: str,
    allowed_hosts: set[str],
    output: Path,
    trust_file: Path,
    workspace_root: Path,
    *,
    bootstrap: bool = False,
    now: datetime | None = None,
    transport=None,
) -> OidcTrustProposal:
    target = _confined(output, workspace_root, ".json")
    trust_target = _confined(trust_file, workspace_root, ".json")
    if target.exists():
        raise ValueError("OIDC trust proposal already exists")
    _metadata, jwks = discover_oidc_trust(
        discovery_endpoint, issuer, allowed_hosts, transport=transport
    )
    canonical_jwks = _canonical_jwks(jwks)
    proposal = OidcTrustProposal(
        project_id=project_id, issuer=issuer, discovery_endpoint=discovery_endpoint,
        bootstrap=bootstrap,
        trust_file=trust_target.relative_to(workspace_root.resolve()).as_posix(),
        key_ids=sorted(key["kid"] for key in jwks.keys),
        jwks_sha256=hashlib.sha256(canonical_jwks).hexdigest(), jwks=jwks,
        proposed_at=now or datetime.now(UTC),
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(proposal.model_dump_json(indent=2).encode() + b"\n")
    return proposal


def apply_approved_oidc_trust_change(
    proposal_file: Path,
    approval_file: Path,
    public_key_file: Path,
    trust_file: Path,
    approval_ledger: Path,
    audit_log: Path,
    workspace_root: Path,
    operator: str,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    proposal_path = _confined(proposal_file, workspace_root, ".json")
    approval_path = _confined(approval_file, workspace_root, ".json")
    trust_path = _confined(trust_file, workspace_root, ".json")
    ledger_path = _confined(approval_ledger, workspace_root, ".db")
    audit_path = _confined(audit_log, workspace_root, ".jsonl")
    proposal_bytes = proposal_path.read_bytes()
    proposal = OidcTrustProposal.model_validate_json(proposal_bytes)
    envelope = SignedApproval.model_validate_json(approval_path.read_bytes())
    public_key_path = _confined(public_key_file, workspace_root, ".key")
    public_key = Ed25519PublicKey.from_public_bytes(public_key_path.read_bytes())
    instant = now or datetime.now(UTC)
    if envelope.claims.reviewer.strip().casefold() == operator.strip().casefold():
        raise ValueError("OIDC trust change requires an independent approver")
    if (
        hashlib.sha256(_canonical_jwks(proposal.jwks)).hexdigest() != proposal.jwks_sha256
        or proposal.key_ids != sorted(key["kid"] for key in proposal.jwks.keys)
        or trust_path.relative_to(workspace_root.resolve()).as_posix() != proposal.trust_file
    ):
        raise ValueError("OIDC trust proposal hash is invalid")
    lock = trust_path.with_name(f".{trust_path.name}.lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock.open("x"):
            previous_hash, new_bytes = _validate_transition(proposal, trust_path)
            if not verify_oidc_trust_audit(audit_path):
                raise ValueError("OIDC trust audit integrity check failed")
            claims = consume_approval(
                envelope, proposal_bytes, public_key, proposal.project_id,
                "oidc-trust-change", instant, ledger_path,
            )
            _atomic_replace(trust_path, new_bytes)
            record = _append_audit(audit_path, {
                "approval_id": str(claims.approval_id), "reviewer": claims.reviewer,
                "operator": operator, "project_id": proposal.project_id,
                "issuer": proposal.issuer, "previous_jwks_sha256": previous_hash,
                "new_jwks_sha256": proposal.jwks_sha256,
                "key_ids": proposal.key_ids, "applied_at": instant.isoformat(),
            })
    finally:
        lock.unlink(missing_ok=True)
    return {"status": "APPLIED", "approval_id": str(claims.approval_id),
            "record_hash": record["record_hash"], "output": str(trust_path)}


def verify_oidc_trust_audit(path: Path) -> bool:
    previous = GENESIS_HASH
    if not path.exists():
        return True
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            payload = record["change"]
            if record["previous_hash"] != previous:
                return False
            expected = _record_hash(previous, payload)
            if record["record_hash"] != expected:
                return False
            previous = expected
        return True
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return False


def _validate_transition(proposal: OidcTrustProposal, trust_path: Path) -> tuple[str, bytes]:
    if trust_path.exists() == proposal.bootstrap:
        raise ValueError("OIDC trust proposal no longer matches current state")
    new_bytes = _canonical_jwks(proposal.jwks) + b"\n"
    previous_hash = GENESIS_HASH
    if trust_path.exists():
        current_bytes = trust_path.read_bytes()
        current = validate_jwk_set(current_bytes)
        if not {key["kid"] for key in current.keys} & set(proposal.key_ids):
            raise ValueError("OIDC JWKS rotation has no trusted overlap")
        previous_hash = hashlib.sha256(current_bytes).hexdigest()
    return previous_hash, new_bytes


def _canonical_jwks(jwks: JwkSet) -> bytes:
    return json.dumps(jwks.model_dump(), sort_keys=True, separators=(",", ":")).encode()


def _atomic_replace(path: Path, content: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _append_audit(path: Path, payload: dict) -> dict:
    previous = GENESIS_HASH
    if path.exists() and path.stat().st_size:
        previous = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])["record_hash"]
    record = {"previous_hash": previous, "record_hash": _record_hash(previous, payload),
              "change": payload}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def _record_hash(previous: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{previous}:{canonical}".encode()).hexdigest()


def _confined(path: Path, root: Path, suffix: str) -> Path:
    resolved = (path if path.is_absolute() else root / path).resolve()
    if resolved.suffix.lower() != suffix or not resolved.is_relative_to(root.resolve()):
        raise ValueError("OIDC trust artifact escapes the workspace")
    return resolved
