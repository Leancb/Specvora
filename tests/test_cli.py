import json
import sys
from pathlib import Path

from specvora.cli import main


def test_cli_reports_generated_artifacts(tmp_path: Path, monkeypatch, capsys) -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Health", "version": "1"},
        "paths": {"/health": {"get": {"responses": {"200": {"description": "ok"}}}}},
    }
    (tmp_path / "openapi.json").write_text(json.dumps(spec), encoding="utf-8")
    project = {
        "project_id": "health-api",
        "requirements": ["Expose health"],
        "openapi_path": "openapi.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
    }
    project_file = tmp_path / "project.json"
    project_file.write_text(json.dumps(project), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["specvora", "analyze", str(project_file), "--workspace-root", str(tmp_path / "ws")],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["project_id"] == "health-api"
    assert len(payload["artifacts"]) == 7
    assert any(path.endswith("request-cases.json") for path in payload["artifacts"])
    assert any(path.endswith("validation-report.json") for path in payload["artifacts"])
    assert any(path.endswith("quality-gate.json") for path in payload["artifacts"])


def test_cli_confines_security_export_and_reads_runtime_token(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state.db"
    state.touch()
    checkpoint = tmp_path / "checkpoint.json"
    captured = {}

    def export(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {"status": "EXPORTED", "exported": 1, "last_event_id": 1}

    monkeypatch.setattr("specvora.cli.export_security_events", export)
    monkeypatch.setenv("SPECVORA_SIEM_TOKEN", "runtime-secret-" + "x" * 32)
    monkeypatch.setattr(sys, "argv", [
        "specvora", "export-security", "--workspace-root", str(tmp_path),
        "--state-db", str(state), "--checkpoint", str(checkpoint),
        "--endpoint", "https://siem.example/events", "--allowed-host", "siem.example",
    ])
    main()
    assert json.loads(capsys.readouterr().out)["exported"] == 1
    assert captured["args"][4].startswith("runtime-secret-")
    assert not checkpoint.exists()
