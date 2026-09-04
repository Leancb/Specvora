"""Detached approval signatures; no execution or automatic trust enrollment."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ApprovalClaims(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["specvora-approval-v1"] = "specvora-approval-v1"
    approval_id: UUID = Field(default_factory=uuid4)
    project_id: str = Field(min_length=1)
    purpose: Literal["proposal-promotion", "release-review"]
    reviewer: str = Field(min_length=3)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    issued_at: AwareDatetime
    expires_at: AwareDatetime


class SignedApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: ApprovalClaims
    signature: str = Field(pattern=r"^[0-9a-f]{128}$")


def _canonical(claims: ApprovalClaims) -> bytes:
    return json.dumps(
        claims.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def sign_approval(
    claims: ApprovalClaims, artifact: bytes, key: Ed25519PrivateKey, approval: str
) -> SignedApproval:
    if approval != "APPROVED_SIGNING":
        raise ValueError("Explicit signing approval is required")
    if claims.expires_at <= claims.issued_at:
        raise ValueError("Approval expiry must follow issuance")
    if hashlib.sha256(artifact).hexdigest() != claims.artifact_sha256:
        raise ValueError("Artifact hash mismatch")
    return SignedApproval(claims=claims, signature=key.sign(_canonical(claims)).hex())


def verify_approval(
    envelope: SignedApproval,
    artifact: bytes,
    trusted_key: Ed25519PublicKey,
    project_id: str,
    purpose: str,
    now: datetime,
) -> ApprovalClaims:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Verification time must include a timezone")
    try:
        trusted_key.verify(bytes.fromhex(envelope.signature), _canonical(envelope.claims))
    except InvalidSignature as exc:
        raise ValueError("Approval signature is invalid") from exc
    claims = envelope.claims
    if claims.project_id != project_id or claims.purpose != purpose:
        raise ValueError("Approval context mismatch")
    if not claims.issued_at <= now < claims.expires_at:
        raise ValueError("Approval is expired or not yet valid")
    if hashlib.sha256(artifact).hexdigest() != claims.artifact_sha256:
        raise ValueError("Artifact hash mismatch")
    return claims


def consume_approval(
    envelope: SignedApproval,
    artifact: bytes,
    trusted_key: Ed25519PublicKey,
    project_id: str,
    purpose: str,
    now: datetime,
    ledger: Path,
) -> ApprovalClaims:
    claims = verify_approval(envelope, artifact, trusted_key, project_id, purpose, now)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(ledger, timeout=5)) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS consumed (approval_id TEXT PRIMARY KEY)")
        try:
            connection.execute("INSERT INTO consumed VALUES (?)", (str(claims.approval_id),))
            connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Approval has already been consumed") from exc
    return claims
