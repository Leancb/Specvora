import json
from pathlib import Path

from specvora.pipeline import run_analysis


def test_pipeline_emits_every_resolved_anyof_variant(tmp_path: Path) -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Contacts", "version": "1"},
        "components": {
            "schemas": {
                "Email": {
                    "type": "object",
                    "required": ["email"],
                    "properties": {"email": {"type": "string", "format": "email"}},
                },
                "Phone": {
                    "type": "object",
                    "required": ["phone"],
                    "properties": {"phone": {"type": "string", "minLength": 10}},
                },
            }
        },
        "paths": {
            "/contacts": {
                "post": {
                    "operationId": "createContact",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "anyOf": [
                                        {"$ref": "#/components/schemas/Email"},
                                        {"$ref": "#/components/schemas/Phone"},
                                    ]
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
        "project_id": "contacts",
        "requirements": ["Create contacts by email or phone"],
        "openapi_path": "openapi.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
    }
    project_file = tmp_path / "project.json"
    project_file.write_text(json.dumps(project), encoding="utf-8")

    run_analysis(project_file, tmp_path / "workspaces")

    cases = json.loads((tmp_path / "workspaces/contacts/generated/request-cases.json").read_text())
    valid_cases = [case for case in cases if case["kind"] == "valid"]
    assert [case["case_id"] for case in valid_cases] == [
        "createContact-valid-anyOf-1",
        "createContact-valid-anyOf-2",
    ]
    assert valid_cases[0]["body"] == {"email": "qa@example.com"}
    assert valid_cases[1]["body"] == {"phone": "xxxxxxxxxx"}
