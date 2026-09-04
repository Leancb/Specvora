import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specvora.combined_release import CombinedReleaseRequest, assess_combined
from specvora.signed_approval import (
    ApprovalClaims,
    consume_approval,
    sign_approval,
    verify_approval,
)


def approval():
    key = Ed25519PrivateKey.generate()
    now = datetime.now(UTC)
    artifact = b'{"reviewer":"Human","decision":"ACCEPT"}'
    claims = ApprovalClaims(
        project_id="demo",
        purpose="proposal-promotion",
        reviewer="Human reviewer",
        artifact_sha256=hashlib.sha256(artifact).hexdigest(),
        issued_at=now,
        expires_at=now + timedelta(hours=1),
    )
    return key, now, artifact, sign_approval(claims, artifact, key, "APPROVED_SIGNING")


def test_signature_roundtrip_and_persistent_single_use(tmp_path: Path) -> None:
    key, now, artifact, envelope = approval()
    args = (envelope, artifact, key.public_key(), "demo", "proposal-promotion", now)
    assert verify_approval(*args).reviewer == "Human reviewer"
    ledger = tmp_path / "used.db"
    consume_approval(*args, ledger=ledger)
    with pytest.raises(ValueError, match="already been consumed"):
        consume_approval(*args, ledger=ledger)
    assert verify_approval(*args).approval_id == envelope.claims.approval_id


@pytest.mark.parametrize("change", ["key", "artifact", "project", "purpose", "expired", "future"])
def test_invalid_approvals_fail_closed(change: str) -> None:
    key, now, artifact, envelope = approval()
    public = key.public_key()
    project, purpose = "demo", "proposal-promotion"
    if change == "key":
        public = Ed25519PrivateKey.generate().public_key()
    elif change == "artifact":
        artifact += b"changed"
    elif change == "project":
        project = "other"
    elif change == "purpose":
        purpose = "release-review"
    elif change == "expired":
        now += timedelta(hours=1)
    else:
        now -= timedelta(seconds=1)
    with pytest.raises(ValueError):
        verify_approval(envelope, artifact, public, project, purpose, now)


def test_signing_requires_authority_and_valid_claims() -> None:
    key, _, artifact, envelope = approval()
    with pytest.raises(ValueError, match="approval"):
        sign_approval(envelope.claims, artifact, key, "APPROVED")
    with pytest.raises(ValueError, match="hash"):
        sign_approval(envelope.claims, b"different", key, "APPROVED_SIGNING")
    claims = envelope.claims.model_copy(update={"expires_at": envelope.claims.issued_at})
    with pytest.raises(ValueError, match="expiry"):
        sign_approval(claims, artifact, key, "APPROVED_SIGNING")


def combined_request(**browser_changes):
    result = dict(
        project_id="demo",
        run_id="api-1",
        total=10,
        passed=10,
        failed=0,
        requirements_total=10,
        requirements_covered=10,
    )
    browser = {**result, "run_id": "web-1", **browser_changes}
    return CombinedReleaseRequest(
        project_id="demo", release_id="release-1", api=result, browser=browser
    )


@pytest.mark.parametrize(
    ("changes", "decision"),
    [
        ({}, "RELEASE"),
        ({"passed": 7, "failed": 3}, "HUMAN_REVIEW"),
        ({"passed": 9, "failed": 1, "critical_failures": 1}, "BLOCK"),
        ({"passed": 0, "failed": 10}, "BLOCK"),
    ],
)
def test_worst_suite_prevails(changes: dict, decision: str) -> None:
    result = assess_combined(combined_request(**changes))
    assert result.decision == decision
    assert result.authority == "recommendation-only"


@pytest.mark.parametrize("changes", [{"project_id": "other"}, {"run_id": "api-1"}])
def test_combined_rejects_mixed_projects_or_reused_runs(changes: dict) -> None:
    with pytest.raises(ValueError):
        assess_combined(combined_request(**changes))


def test_governance_cli_roundtrip_and_immutable_output(tmp_path: Path, monkeypatch, capsys) -> None:
    from specvora.governance_cli import main

    key, _, artifact, envelope = approval()
    (tmp_path / "private.key").write_bytes(key.private_bytes_raw())
    (tmp_path / "public.key").write_bytes(key.public_key().public_bytes_raw())
    (tmp_path / "artifact.json").write_bytes(artifact)
    (tmp_path / "claims.json").write_text(envelope.claims.model_dump_json(), encoding="utf-8")

    def run(*args):
        monkeypatch.setattr(sys, "argv", ["governance", "--workspace-root", str(tmp_path), *args])
        main()
        return json.loads(capsys.readouterr().out)

    signed = str(tmp_path / "signed.json")
    sign_args = (
        "sign",
        str(tmp_path / "claims.json"),
        "--artifact",
        str(tmp_path / "artifact.json"),
        "--private-key",
        str(tmp_path / "private.key"),
        "--approval",
        "APPROVED_SIGNING",
        "--output",
        signed,
    )
    assert run(*sign_args)["output"] == str(Path(signed).resolve())
    with pytest.raises(FileExistsError):
        run(*sign_args)
    verification = (
        signed,
        "--artifact",
        str(tmp_path / "artifact.json"),
        "--public-key",
        str(tmp_path / "public.key"),
        "--project-id",
        "demo",
        "--purpose",
        "proposal-promotion",
    )
    assert run("verify", *verification) == {"valid": True, "consumed": False}
    assert run("consume", *verification, "--ledger", str(tmp_path / "used.db"))["consumed"]
    combined = tmp_path / "combined.json"
    combined.write_text(combined_request().model_dump_json(), encoding="utf-8")
    run("assess-combined", str(combined), "--output", str(tmp_path / "result.json"))
    assert json.loads((tmp_path / "result.json").read_text())["decision"] == "RELEASE"


def test_claim_tampering_and_naive_clock_rejected() -> None:
    key, now, artifact, envelope = approval()
    changed = envelope.model_copy(
        update={"claims": envelope.claims.model_copy(update={"reviewer": "Someone else"})}
    )
    with pytest.raises(ValueError, match="signature"):
        verify_approval(changed, artifact, key.public_key(), "demo", "proposal-promotion", now)
    with pytest.raises(ValueError, match="timezone"):
        verify_approval(
            envelope,
            artifact,
            key.public_key(),
            "demo",
            "proposal-promotion",
            now.replace(tzinfo=None),
        )


def test_concurrent_consumption_accepts_only_one(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    key, now, artifact, envelope = approval()

    def consume():
        try:
            consume_approval(
                envelope,
                artifact,
                key.public_key(),
                "demo",
                "proposal-promotion",
                now,
                tmp_path / "concurrent.db",
            )
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: consume(), range(2)))
    assert sorted(outcomes) == [False, True]
