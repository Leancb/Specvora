from pathlib import Path


def test_oidc_alert_workflow_uses_runtime_secret_and_has_no_rotation_authority():
    script = Path("scripts/monitor-and-alert-oidc.ps1").read_text(encoding="utf-8")
    assert "$env:SPECVORA_OIDC_ALERT_TOKEN" in script
    assert "specvora.oidc_monitor_cli" in script
    assert "specvora.oidc_alert_cli" in script
    assert "$monitorExit -notin @(0, 10, 20)" in script
    assert "update-oidc-trust" not in script
    assert "apply-oidc-trust" not in script
