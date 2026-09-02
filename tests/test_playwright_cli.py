import json
import subprocess
import sys
from pathlib import Path

from specvora.cli import main
from specvora.pipeline import run_analysis


def test_cli_runs_approved_playwright_with_controlled_runner(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Web", "version": "1"},
        "paths": {"/health": {"get": {"responses": {"200": {"description": "ok"}}}}},
    }
    (tmp_path / "openapi.json").write_text(json.dumps(spec), encoding="utf-8")
    project = {
        "project_id": "web-demo",
        "requirements": ["Sign in"],
        "openapi_path": "openapi.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
        "web_base_url": "http://localhost:3000",
        "web_journeys": [
            {
                "journey_id": "sign-in",
                "title": "Sign in",
                "steps": [{"action": "goto", "path": "/login"}],
            }
        ],
    }
    project_file = tmp_path / "project.json"
    project_file.write_text(json.dumps(project), encoding="utf-8")
    workspace = tmp_path / "workspaces"
    run_analysis(project_file, workspace)

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps({"stats": {"expected": 1}}), stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    report = workspace / "web-demo/runs/playwright.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "specvora",
            "run-playwright",
            "--workspace-root",
            str(workspace),
            "--generated-dir",
            str(workspace / "web-demo/generated"),
            "--report-out",
            str(report),
            "--web-base-url",
            "http://localhost:3000",
            "--allowed-host",
            "localhost",
            "--approval",
            "APPROVED_PLAYWRIGHT",
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["run"]["exit_code"] == 0
    assert payload["run"]["report_path"] == str(report)
    assert report.is_file()
