import json
from pathlib import Path

import pytest

from specvora.pipeline import run_analysis


def test_pipeline_generates_traceable_owned_artifacts(tmp_path: Path) -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Pets", "version": "1"},
        "paths": {
            "/pets/{petId}": {
                "get": {
                    "operationId": "getPet",
                    "parameters": [{"name": "petId", "in": "path", "required": True}],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    (tmp_path / "openapi.json").write_text(json.dumps(spec), encoding="utf-8")
    project = {
        "project_id": "petstore",
        "requirements": ["Retrieve a pet by id"],
        "openapi_path": "openapi.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
    }
    project_file = tmp_path / "project.json"
    project_file.write_text(json.dumps(project), encoding="utf-8")
    result, files = run_analysis(project_file, tmp_path / "workspaces")
    assert [scenario.kind for scenario in result.scenarios] == ["positive", "negative"]
    assert result.traceability[0]["requirement_id"] == "REQ-001"
    assert {path.name for path in files} == {
        "quality-plan.json",
        "traceability.json",
        "request-cases.json",
        "validation-report.json",
        "quality-gate.json",
        "test_generated_api.py",
        "github-actions.yml",
    }
    assert (
        "Review and approve"
        in (tmp_path / "workspaces/petstore/generated/test_generated_api.py").read_text()
    )


def test_pipeline_rejects_non_openapi_document(tmp_path: Path) -> None:
    (tmp_path / "bad.yaml").write_text("swagger: '2.0'", encoding="utf-8")
    project = {
        "project_id": "invalid",
        "requirements": ["Reject unsupported contracts"],
        "openapi_path": "bad.yaml",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
    }
    project_file = tmp_path / "project.json"
    project_file.write_text(json.dumps(project), encoding="utf-8")
    with pytest.raises(ValueError, match=r"Only OpenAPI 3\.x"):
        run_analysis(project_file, tmp_path / "workspaces")
