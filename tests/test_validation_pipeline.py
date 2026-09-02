import json
from pathlib import Path

from specvora.pipeline import run_analysis


def test_pipeline_writes_validation_report_for_generated_cases(tmp_path: Path) -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Users", "version": "1"},
        "paths": {
            "/users": {
                "post": {
                    "operationId": "createUser",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {"name": {"type": "string", "minLength": 2}},
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "created"}},
                }
            }
        },
    }
    (tmp_path / "openapi.json").write_text(json.dumps(spec), encoding="utf-8")
    project = {
        "project_id": "users",
        "requirements": ["Create users"],
        "openapi_path": "openapi.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
    }
    project_file = tmp_path / "project.json"
    project_file.write_text(json.dumps(project), encoding="utf-8")

    _, files = run_analysis(project_file, tmp_path / "workspaces")

    assert "validation-report.json" in {path.name for path in files}
    report = json.loads(
        (tmp_path / "workspaces/users/generated/validation-report.json").read_text()
    )
    assert report == [
        {
            "operation_id": "createUser",
            "cases_checked": 3,
            "valid": True,
            "findings": [],
        }
    ]
