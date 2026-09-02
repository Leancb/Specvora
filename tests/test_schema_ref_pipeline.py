import json
from pathlib import Path

import pytest

from specvora.pipeline import run_analysis
from specvora.schema_resolver import SchemaResolutionError


def project_file(tmp_path: Path, spec: dict[str, object]) -> Path:
    (tmp_path / "openapi.json").write_text(json.dumps(spec), encoding="utf-8")
    project = {
        "project_id": "users",
        "requirements": ["Create users"],
        "openapi_path": "openapi.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
    }
    path = tmp_path / "project.json"
    path.write_text(json.dumps(project), encoding="utf-8")
    return path


def test_pipeline_generates_data_from_internal_component_reference(tmp_path: Path) -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Users", "version": "1"},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["email", "id"],
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "id": {"type": "string", "format": "uuid"},
                    },
                }
            }
        },
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/User"}}
                        }
                    },
                    "responses": {"201": {"description": "created"}},
                }
            }
        },
    }
    _, _ = run_analysis(project_file(tmp_path, spec), tmp_path / "workspaces")
    cases = json.loads((tmp_path / "workspaces/users/generated/request-cases.json").read_text())
    assert cases[0]["body"] == {
        "email": "qa@example.com",
        "id": "00000000-0000-4000-8000-000000000001",
    }


def test_pipeline_rejects_remote_schema_reference(tmp_path: Path) -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Users", "version": "1"},
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "https://example.com/user.json"}
                            }
                        }
                    },
                    "responses": {"201": {"description": "created"}},
                }
            }
        },
    }
    with pytest.raises(SchemaResolutionError, match="Only internal"):
        run_analysis(project_file(tmp_path, spec), tmp_path / "workspaces")
