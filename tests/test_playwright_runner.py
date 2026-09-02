import json
import subprocess
from pathlib import Path

import pytest

from specvora.playwright_runner import PlaywrightRunnerRequest, run_generated_playwright
from specvora.runner import RunnerError


def runner_request(tmp_path: Path, **overrides: object) -> PlaywrightRunnerRequest:
    generated = tmp_path / "project/generated"
    playwright = generated / "playwright"
    playwright.mkdir(parents=True, exist_ok=True)
    (generated / "quality-gate.json").write_text(
        json.dumps({"status": "READY_FOR_HUMAN_APPROVAL"}), encoding="utf-8"
    )
    for name in ("test_generated_web.spec.ts", "playwright.config.ts", "package.json"):
        (playwright / name).write_text("generated\n", encoding="utf-8")
    (playwright / "playwright-plan.json").write_text(
        json.dumps(
            {
                "base_url": "http://localhost:3000/",
                "allowed_hosts": ["localhost"],
                "journeys": [],
                "authority": "human-review-required",
            }
        ),
        encoding="utf-8",
    )
    values = {
        "workspace_root": tmp_path,
        "generated_dir": generated,
        "report_path": tmp_path / "project/runs/playwright-report.json",
        "web_base_url": "http://localhost:3000",
        "allowed_hosts": ["localhost"],
        "approval": "APPROVED_PLAYWRIGHT",
        "timeout_seconds": 10,
    }
    values.update(overrides)
    return PlaywrightRunnerRequest.model_validate(values)


def test_runner_uses_fixed_command_filtered_environment_and_no_shell(
    tmp_path: Path, monkeypatch
) -> None:
    request = runner_request(tmp_path)
    captured = {}

    def fake_run(command, **kwargs):
        captured.update({"command": command, **kwargs})
        report = {"stats": {"expected": 1}, "suites": []}
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(report), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-leak")
    outcome = run_generated_playwright(request)
    assert captured["shell"] is False
    assert captured["command"][1:] == [
        "playwright",
        "test",
        "test_generated_web.spec.ts",
        "--config=playwright.config.ts",
        "--reporter=json",
    ]
    assert "OPENAI_API_KEY" not in captured["env"]
    assert captured["env"]["CI"] == "1"
    assert json.loads(request.report_path.read_text())["stats"]["expected"] == 1
    assert outcome.exit_code == 0


def test_runner_requires_dedicated_approval_allowlist_and_confined_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="Playwright approval"):
        run_generated_playwright(runner_request(tmp_path, approval="APPROVED"))
    with pytest.raises(ValueError, match="not allowed"):
        run_generated_playwright(
            runner_request(tmp_path, web_base_url="https://production.example.com")
        )
    with pytest.raises(ValueError, match="escapes"):
        run_generated_playwright(
            runner_request(tmp_path, report_path=tmp_path.parent / "report.json")
        )
    with pytest.raises(ValueError, match="must not overwrite"):
        run_generated_playwright(
            runner_request(
                tmp_path,
                report_path=tmp_path / "project/generated/playwright/package.json",
            )
        )


def test_runner_rejects_plan_or_gate_drift(tmp_path: Path) -> None:
    request = runner_request(tmp_path, allowed_hosts=["localhost", "cdn.example"])
    with pytest.raises(ValueError, match="allowlist differs"):
        run_generated_playwright(request)
    request = runner_request(tmp_path, web_base_url="http://localhost:4000")
    with pytest.raises(ValueError, match="base URL differs"):
        run_generated_playwright(request)
    request = runner_request(tmp_path)
    (request.generated_dir / "quality-gate.json").write_text(
        json.dumps({"status": "BLOCKED"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="blocks"):
        run_generated_playwright(request)


def test_runner_fails_closed_for_timeout_or_invalid_report(tmp_path: Path, monkeypatch) -> None:
    request = runner_request(tmp_path)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=1)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RunnerError, match="timed out"):
        run_generated_playwright(request)

    def invalid_report(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="not json", stderr="failed")

    monkeypatch.setattr(subprocess, "run", invalid_report)
    with pytest.raises(RunnerError, match="required JSON report"):
        run_generated_playwright(request)
