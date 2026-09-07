from pathlib import Path


def test_oidc_trust_script_requires_explicit_operator_approval():
    script = Path("scripts/update-oidc-trust.ps1").read_text(encoding="utf-8")
    assert "[switch]$ApproveTrustUpdate" in script
    assert "if (-not $ApproveTrustUpdate)" in script
    assert '"--allowed-host", $hostName' in script
    assert '"--workspace-root", $WorkspaceRoot' in script
