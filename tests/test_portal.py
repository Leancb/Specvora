import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from specvora.ai_proposals import AIProposalEnvelope, AIProposedScenario, proposal_input_sha256
from specvora.main import app
from specvora.repository import ProjectRepository


def workspace(tmp_path: Path) -> tuple[Path, Path]:
    specification = {
        "openapi": "3.0.3",
        "info": {"title": "Pets", "version": "1"},
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "listPets",
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    (tmp_path / "openapi.json").write_text(json.dumps(specification), encoding="utf-8")
    project_file = tmp_path / "project.json"
    project_file.write_text(
        json.dumps(
            {
                "project_id": "portal-demo",
                "requirements": ["Consumers can list pets"],
                "openapi_path": "openapi.json",
                "base_url": "http://localhost:8080",
                "allowed_hosts": ["localhost"],
            }
        ),
        encoding="utf-8",
    )
    proposal_file = tmp_path / "proposals/ready.json"
    proposal_file.parent.mkdir()
    envelope = AIProposalEnvelope(
        model="test-model",
        input_sha256=proposal_input_sha256(project_file),
        created_at=datetime(2026, 9, 3, tzinfo=UTC),
        status="READY_FOR_HUMAN_REVIEW",
        findings=[],
        proposals=[
            AIProposedScenario(
                proposal_id="AI-001",
                requirement="Consumers can list pets",
                operation_id="listPets",
                kind="negative",
                title="Service throttles excess traffic",
                rationale="Adds resilience coverage",
                expected_statuses=[429],
            )
        ],
    )
    proposal_file.write_text(envelope.model_dump_json(indent=2), encoding="utf-8")
    return project_file, proposal_file


def test_repository_persists_multiple_projects_and_filters_reviews(tmp_path: Path) -> None:
    store = ProjectRepository(tmp_path / "state/specvora.db")
    store.add_project("alpha", tmp_path / "a.json", tmp_path)
    store.add_project("beta", tmp_path / "b.json", tmp_path)
    store.add_review("review-alpha", "alpha", tmp_path / "proposal.json", "a" * 64)
    assert [item["project_id"] for item in store.list_projects()] == ["alpha", "beta"]
    assert [item["review_id"] for item in store.list_reviews("PENDING")] == ["review-alpha"]


def test_portal_registers_reviews_and_preserves_human_authority(
    tmp_path: Path, monkeypatch
) -> None:
    project_file, proposal_file = workspace(tmp_path)
    monkeypatch.setenv("SPECVORA_DB_PATH", str(tmp_path / "state/specvora.db"))
    client = TestClient(app)
    response = client.post(
        "/api/projects",
        json={"project_file": str(project_file), "workspace_root": str(tmp_path)},
    )
    assert response.status_code == 201
    response = client.post(
        "/api/reviews",
        json={
            "review_id": "review-001",
            "project_id": "portal-demo",
            "proposal_file": str(proposal_file),
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"
    response = client.post(
        "/api/reviews/review-001/decision",
        json={
            "reviewer": "Leandro do Couto Brum",
            "approval": "APPROVED_PROPOSAL_PROMOTION",
            "decisions": [
                {
                    "proposal_id": "AI-001",
                    "decision": "ACCEPT",
                    "rationale": "Approved for the next governed generation stage",
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["review"]["status"] == "REVIEWED"
    assert response.json()["promotion"]["scenarios"][0]["source_proposal_id"] == "AI-001"
    assert (
        client.post(
            "/api/reviews/review-001/decision",
            json={
                "reviewer": "Leandro do Couto Brum",
                "approval": "APPROVED_PROPOSAL_PROMOTION",
                "decisions": [
                    {
                        "proposal_id": "AI-001",
                        "decision": "REJECT",
                        "rationale": "Not approved",
                    }
                ],
            },
        ).status_code
        == 400
    )


def test_portal_rejects_files_outside_workspace_and_exposes_local_warning(
    tmp_path: Path, monkeypatch
) -> None:
    project_file, _ = workspace(tmp_path)
    root = tmp_path / "confined"
    root.mkdir()
    monkeypatch.setenv("SPECVORA_DB_PATH", str(tmp_path / "state/specvora.db"))
    client = TestClient(app)
    response = client.post(
        "/api/projects",
        json={"project_file": str(project_file), "workspace_root": str(root)},
    )
    assert response.status_code == 400
    portal = client.get("/portal")
    assert portal.status_code == 200
    assert "Local training portal" in portal.text
    assert r"join('\n')" in portal.text


def test_portal_rejects_openapi_reference_outside_workspace(tmp_path: Path, monkeypatch) -> None:
    project_file, _ = workspace(tmp_path)
    confined = tmp_path / "confined"
    confined.mkdir()
    confined_project = confined / "project.json"
    payload = json.loads(project_file.read_text(encoding="utf-8"))
    payload["openapi_path"] = "../openapi.json"
    confined_project.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("SPECVORA_DB_PATH", str(tmp_path / "state/specvora.db"))
    response = TestClient(app).post(
        "/api/projects",
        json={"project_file": str(confined_project), "workspace_root": str(confined)},
    )
    assert response.status_code == 400
    assert "OpenAPI" in response.json()["detail"]


def test_portal_lists_cases_and_generates_without_execution(tmp_path: Path, monkeypatch) -> None:
    project_file, proposal_file = workspace(tmp_path)
    specification = json.loads((tmp_path / "openapi.json").read_text())
    operation = specification["paths"]["/pets"]["get"]
    operation["responses"]["429"] = {"description": "controlled rate limit"}
    operation["x-specvora-test-fixtures"] = {
        "429": {
            "kind": "request-header",
            "name": "X-Specvora-Fixture",
            "value": "rate-limit",
        }
    }
    (tmp_path / "openapi.json").write_text(json.dumps(specification))
    monkeypatch.setenv("SPECVORA_DB_PATH", str(tmp_path / "state/specvora.db"))
    client = TestClient(app)
    assert (
        client.post(
            "/api/projects",
            json={"project_file": str(project_file), "workspace_root": str(tmp_path)},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/reviews",
            json={
                "review_id": "review-portal",
                "project_id": "portal-demo",
                "proposal_file": str(proposal_file),
            },
        ).status_code
        == 201
    )
    pending = client.get("/api/reviews/review-portal/generation")
    assert pending.status_code == 400
    decision = {
        "reviewer": "Leandro do Couto Brum",
        "approval": "APPROVED_PROPOSAL_PROMOTION",
        "decisions": [{"proposal_id": "AI-001", "decision": "ACCEPT", "rationale": "ACCEPT"}],
    }
    assert client.post("/api/reviews/review-portal/decision", json=decision).status_code == 200
    detail = client.get("/api/reviews/review-portal/generation")
    assert detail.status_code == 200
    assert detail.json()["cases"]["listPets"][0]["case_id"] == "listPets-valid"
    request = {
        "plan_id": "plan-portal-001",
        "bindings": [{"scenario_id": "PROM-AI-001", "case_id": "listPets-valid"}],
    }
    generated = client.post("/api/reviews/review-portal/generation", json=request)
    assert generated.status_code == 201
    assert generated.json()["status"] == "READY_FOR_HUMAN_APPROVAL"
    assert generated.json()["tests_generated"] == 1
    output = tmp_path / "workspaces/portal-demo/promoted-generated/plan-portal-001"
    assert (output / "test_generated_api.py").is_file()
    assert not (output / "pytest-report.json").exists()
    duplicate = client.post("/api/reviews/review-portal/generation", json=request)
    assert duplicate.status_code == 400
    assert "already exists" in duplicate.json()["detail"]
