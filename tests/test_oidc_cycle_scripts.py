from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_cycle_script_uses_runtime_token_and_leased_cli():
    script = (ROOT / "scripts/run-oidc-monitor-cycle.ps1").read_text(encoding="utf-8")
    assert "SPECVORA_OIDC_ALERT_TOKEN" in script
    assert "specvora-oidc-cycle" in script
    assert "update-oidc" not in script.lower()
    assert "apply-oidc" not in script.lower()


def test_task_registration_requires_explicit_approval_and_ignores_overlap():
    script = (ROOT / "scripts/register-oidc-monitor-task.ps1").read_text(encoding="utf-8")
    assert "ApproveTaskRegistration" in script
    assert "MultipleInstances IgnoreNew" in script
    assert "ExecutionTimeLimit" in script
    assert "Register-ScheduledTask" in script
    assert "update-oidc" not in script.lower()
    assert "apply-oidc" not in script.lower()
