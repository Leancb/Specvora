from pathlib import Path


def test_oidc_governance_scripts_keep_discovery_signing_and_application_separate():
    prepare = Path("scripts/prepare-oidc-trust-change.ps1").read_text(encoding="utf-8")
    apply = Path("scripts/apply-oidc-trust-change.ps1").read_text(encoding="utf-8")
    assert "[switch]$ApproveDiscovery" in prepare
    assert "prepare-approval" in prepare
    assert "Sign the claims offline" in prepare
    assert "private" not in apply.casefold()
    assert "[switch]$ApproveApplication" in apply
    assert "--operator $Operator" in apply
