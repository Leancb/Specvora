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
    assert len(payload["artifacts"]) == 5
    assert any(path.endswith("request-cases.json") for path in payload["artifacts"])
