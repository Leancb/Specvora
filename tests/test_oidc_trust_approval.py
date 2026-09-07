import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_oidc_trust import jwk, transport_for

from specvora.oidc_trust_approval import (
    apply_approved_oidc_trust_change,
    propose_oidc_trust_change,
    verify_oidc_trust_audit,
)
from specvora.signed_approval import ApprovalClaims, sign_approval


def proposal(tmp_path, *, key=None):
    proposed = tmp_path / "changes/proposal.json"
    trust = tmp_path / "trust/jwks.json"
    propose_oidc_trust_change(
        "portal", "https://identity.example/tenant/.well-known/openid-configuration",
        "https://identity.example/tenant", {"identity.example", "keys.example"},
        proposed, trust, tmp_path, bootstrap=True,
        now=datetime(2026, 9, 7, tzinfo=UTC), transport=transport_for([key or jwk("key-a")]),
    )
    return proposed, trust


def approve(tmp_path, proposed, reviewer="Security Reviewer"):
    private = Ed25519PrivateKey.generate()
    public = tmp_path / "keys/reviewer-public.key"
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_bytes(private.public_key().public_bytes_raw())
    now = datetime(2026, 9, 7, 1, tzinfo=UTC)
    artifact = proposed.read_bytes()
    claims = ApprovalClaims(
        project_id="portal", purpose="oidc-trust-change", reviewer=reviewer,
        artifact_sha256=hashlib.sha256(artifact).hexdigest(), issued_at=now,
        expires_at=now + timedelta(minutes=15),
    )
    signed = sign_approval(claims, artifact, private, "APPROVED_SIGNING")
    approval = tmp_path / "changes/approval.json"
    approval.write_text(signed.model_dump_json(), encoding="utf-8")
    return approval, public, now


def apply(tmp_path, proposed, trust, approval, public, now, *, operator="Operations User"):
    return apply_approved_oidc_trust_change(
        proposed, approval, public, trust, tmp_path / "state/approvals.db",
        tmp_path / "audit/oidc-trust.jsonl", tmp_path, operator, now=now,
    )


def test_independent_approval_applies_and_audits_exact_proposal(tmp_path):
    proposed, trust = proposal(tmp_path)
    approval, public, now = approve(tmp_path, proposed)
    result = apply(tmp_path, proposed, trust, approval, public, now)
    assert result["status"] == "APPLIED"
    assert json.loads(trust.read_text())["keys"][0]["kid"] == "key-a"
    assert verify_oidc_trust_audit(tmp_path / "audit/oidc-trust.jsonl")
    record = json.loads((tmp_path / "audit/oidc-trust.jsonl").read_text())
    assert record["change"]["reviewer"] == "Security Reviewer"
    assert record["change"]["operator"] == "Operations User"


def test_self_approval_and_wrong_target_are_rejected_before_mutation(tmp_path):
    proposed, trust = proposal(tmp_path)
    approval, public, now = approve(tmp_path, proposed, reviewer="Same Person")
    with pytest.raises(ValueError, match="independent"):
        apply(tmp_path, proposed, trust, approval, public, now, operator=" same person ")
    assert not trust.exists()
    with pytest.raises(ValueError, match="proposal hash"):
        apply_approved_oidc_trust_change(
            proposed, approval, public, tmp_path / "trust/other.json",
            tmp_path / "state/approvals.db", tmp_path / "audit/log.jsonl",
            tmp_path, "Operations User", now=now,
        )


def test_approval_is_consumed_once_even_for_an_identical_restored_target(tmp_path):
    proposed, trust = proposal(tmp_path)
    approval, public, now = approve(tmp_path, proposed)
    apply(tmp_path, proposed, trust, approval, public, now)
    trust.unlink()
    with pytest.raises(ValueError, match="already been consumed"):
        apply(tmp_path, proposed, trust, approval, public, now)
    assert not trust.exists()


def test_tampered_audit_blocks_next_change(tmp_path):
    proposed, trust = proposal(tmp_path)
    approval, public, now = approve(tmp_path, proposed)
    apply(tmp_path, proposed, trust, approval, public, now)
    audit = tmp_path / "audit/oidc-trust.jsonl"
    audit.write_text(audit.read_text().replace("Operations User", "Intruder"), encoding="utf-8")
    assert not verify_oidc_trust_audit(audit)


def test_overlapping_rotation_extends_audit_chain(tmp_path):
    first = jwk("key-a")
    proposed, trust = proposal(tmp_path, key=first)
    approval, public, now = approve(tmp_path, proposed)
    apply(tmp_path, proposed, trust, approval, public, now)
    rotated = tmp_path / "changes/rotation.json"
    propose_oidc_trust_change(
        "portal", "https://identity.example/tenant/.well-known/openid-configuration",
        "https://identity.example/tenant", {"identity.example", "keys.example"},
        rotated, trust, tmp_path, bootstrap=False, now=now,
        transport=transport_for([first, jwk("key-b")]),
    )
    approval, public, later = approve(tmp_path, rotated)
    apply(tmp_path, rotated, trust, approval, public, later)
    audit = tmp_path / "audit/oidc-trust.jsonl"
    assert verify_oidc_trust_audit(audit)
    assert len(audit.read_text().splitlines()) == 2
