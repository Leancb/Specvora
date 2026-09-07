from pathlib import Path


def test_oidc_monitor_script_is_read_only_and_surfaces_alerts():
    script = Path("scripts/check-oidc-trust.ps1").read_text(encoding="utf-8")
    assert "specvora.oidc_monitor_cli" in script
    assert "requires independent human review" in script
    assert "blocking condition" in script
    assert "update-oidc-trust" not in script
    assert "apply-oidc-trust" not in script
