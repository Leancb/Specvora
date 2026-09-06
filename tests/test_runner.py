import json
import subprocess
from pathlib import Path

import pytest

from specvora.runner import RunnerError, RunnerRequest, run_generated_tests


def runner_request(tmp_path: Path, **overrides: object) -> RunnerRequest:
    generated = tmp_path / "project/generated"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "test_generated_api.py").write_text(
        "def test_ok(): assert True\n", encoding="utf-8"
    )
    (generated / "quality-gate.json").write_text(
        json.dumps({"status": "READY_FOR_HUMAN_APPROVAL"}), encoding="utf-8"
    )
    values = {
        "workspace_root": tmp_path,
        "generated_dir": generated,
        "report_path": tmp_path / "project/runs/report.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
        "approval": "APPROVED",
        "timeout_seconds": 10,
    }
    values.update(overrides)
    return RunnerRequest.model_validate(values)


def test_runner_uses_fixed_command_filtered_environment_and_no_shell(
    tmp_path: Path, monkeypatch
) -> None:
    request = runner_request(tmp_path)
    captured = {}

    def fake_run(command, **kwargs):
        captured.update({"command": command, **kwargs})
        request.report_path.parent.mkdir(parents=True, exist_ok=True)
        request.report_path.write_text('{"tests": []}', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-leak")
    monkeypatch.setenv("SPECVORA_GITHUB_LEDGER_TOKEN", "must-not-leak")
    outcome = run_generated_tests(request)
    assert captured["shell"] is False
    assert captured["command"][1:3] == ["-m", "pytest"]
    assert "--json-report" in captured["command"]
    assert "OPENAI_API_KEY" not in captured["env"]
    assert "SPECVORA_GITHUB_LEDGER_TOKEN" not in captured["env"]
    assert captured["env"]["SPECVORA_BASE_URL"] == "http://localhost:8080"
    assert outcome.exit_code == 0


def test_runner_requires_approval_allowlist_and_confined_report(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="approval"):
        run_generated_tests(runner_request(tmp_path, approval="yes"))
    with pytest.raises(ValueError, match="not allowed"):
        run_generated_tests(runner_request(tmp_path, base_url="https://production.example.com"))
    with pytest.raises(RunnerError, match="escapes"):
        run_generated_tests(runner_request(tmp_path, report_path=tmp_path.parent / "report.json"))


def test_runner_reports_timeout(tmp_path: Path, monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=1)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RunnerError, match="timed out"):
        run_generated_tests(runner_request(tmp_path, timeout_seconds=1))


def test_runner_resolves_referenced_credential_only_into_child_environment(
    tmp_path: Path, monkeypatch
) -> None:
    request = runner_request(tmp_path, credential_ref={"alias": "staging-api"})
    secret = "operator-owned-secret-value"
    captured = {}

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        request.report_path.parent.mkdir(parents=True, exist_ok=True)
        request.report_path.write_text('{"tests": []}', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout=f"token={secret}", stderr="")

    monkeypatch.setenv("SPECVORA_CREDENTIAL_STAGING_API", secret)
    monkeypatch.setattr(subprocess, "run", fake_run)
    outcome = run_generated_tests(request)
    assert captured["env"]["SPECVORA_RUNTIME_AUTHORIZATION"] == f"Bearer {secret}"
    assert secret not in outcome.stdout
    assert "[REDACTED]" in outcome.stdout
    assert secret not in request.model_dump_json()


def test_runner_fails_before_subprocess_for_missing_or_invalid_credential(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("Must not execute"))
    request = runner_request(tmp_path, credential_ref={"alias": "staging-api"})
    with pytest.raises(RuntimeError, match="unavailable"):
        run_generated_tests(request)
    monkeypatch.setenv("SPECVORA_CREDENTIAL_STAGING_API", "short")
    with pytest.raises(RuntimeError, match="invalid"):
        run_generated_tests(request)


def test_credential_alias_is_bound_into_execution_action(tmp_path: Path) -> None:
    from specvora.authorization import execution_action
    from specvora.credential_broker import CredentialReference

    first = runner_request(tmp_path, credential_ref={"alias": "staging-api"})
    action = execution_action(first, "api")
    first.credential_ref = CredentialReference(alias="other-api")
    assert execution_action(first, "api") != action
