import json
from pathlib import Path

from specvora.pipeline import run_analysis


def test_pipeline_writes_request_cases_from_openapi_schema(tmp_path: Path) -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Users", "version": "1"},
        "paths": {
            "/users": {
                "post": {
                    "operationId": "createUser",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {"name": {"type": "string", "minLength": 2}},
                                }
                            }
                        },
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
    assert "request-cases.json" in {path.name for path in files}
    cases = json.loads((tmp_path / "workspaces/users/generated/request-cases.json").read_text())
    assert [case["kind"] for case in cases] == ["valid", "missing_required", "invalid_boundary"]
    assert cases[0]["body"] == {"name": "xx"}
