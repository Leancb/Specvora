import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from specvora.ai_proposals import (
    AIProposalEnvelope,
    AIProposedScenario,
    ProposalFinding,
    proposal_input_sha256,
)
from specvora.cli import main
from specvora.proposal_review import review_and_promote


def proposed(proposal_id: str, title: str) -> AIProposedScenario:
    return AIProposedScenario(
        proposal_id=proposal_id,
        requirement="Consumers can retrieve a pet",
        operation_id="getPet",
        kind="negative",
        title=title,
        rationale="Adds a reviewed edge case",
        expected_statuses=[429],
    )


def write_project(tmp_path: Path) -> Path:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Pets", "version": "1"},
        "paths": {
            "/pets/{petId}": {
                "get": {
                    "operationId": "getPet",
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    (tmp_path / "openapi.json").write_text(json.dumps(spec), encoding="utf-8")
    project = {
        "project_id": "pet-demo",
        "requirements": ["Consumers can retrieve a pet"],
        "openapi_path": "openapi.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
    }
    path = tmp_path / "project.json"
    path.write_text(json.dumps(project), encoding="utf-8")
    return path


def write_proposal(tmp_path: Path, blocked: bool = False) -> Path:
    project_path = write_project(tmp_path)
    finding = ProposalFinding(
        proposal_id="AI-001",
        code="UNKNOWN_OPERATION",
        message="blocked",
    )
    envelope = AIProposalEnvelope(
        model="test-model",
        input_sha256=proposal_input_sha256(project_path),
        created_at=datetime(2026, 9, 3, tzinfo=UTC),
        status="BLOCKED" if blocked else "READY_FOR_HUMAN_REVIEW",
        findings=[finding] if blocked else [],
        proposals=[
            proposed("AI-001", "Rate limiting is enforced"),
            proposed("AI-002", "Dependency failure is mapped"),
        ],
    )
    path = tmp_path / "proposals/ai.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(envelope.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def write_decision(
    tmp_path: Path,
    decisions: list[dict[str, str]] | None = None,
    approval: str = "APPROVED_PROPOSAL_PROMOTION",
) -> Path:
    payload = {
        "reviewer": "Leandro do Couto Brum",
        "approval": approval,
        "decisions": decisions
        or [
            {
                "proposal_id": "AI-001",
                "decision": "ACCEPT",
                "rationale": "Relevant resilience coverage",
            },
            {
                "proposal_id": "AI-002",
                "decision": "REJECT",
                "rationale": "Outside the current API contract",
            },
        ],
    }
    path = tmp_path / "reviews/decision.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def paths(tmp_path: Path) -> tuple[Path, Path]:
    return tmp_path / "reviews/record.json", tmp_path / "promoted/scenarios.json"


def test_review_promotes_only_accepted_and_hashes_both_inputs(tmp_path: Path) -> None:
    proposal_path = write_proposal(tmp_path)
    decision_path = write_decision(tmp_path)
    review_path, catalog_path = paths(tmp_path)
    review, catalog = review_and_promote(
        tmp_path / "project.json",
        proposal_path,
        decision_path,
        review_path,
        catalog_path,
        tmp_path,
    )
    assert review.status == "PROMOTED"
    assert review.accepted == 1
    assert review.rejected == 1
    assert catalog.authority == "human-approved"
    assert [scenario.source_proposal_id for scenario in catalog.scenarios] == ["AI-001"]
    assert catalog.scenarios[0].scenario_id == "PROM-AI-001"
    assert review.source_proposal_sha256 == hashlib.sha256(proposal_path.read_bytes()).hexdigest()
    assert review.review_decision_sha256 == hashlib.sha256(decision_path.read_bytes()).hexdigest()
    assert review_path.is_file() and catalog_path.is_file()


def test_review_can_reject_every_proposal_without_promotion(tmp_path: Path) -> None:
    rejected = [
        {
            "proposal_id": proposal_id,
            "decision": "REJECT",
            "rationale": "Not selected for this release",
        }
        for proposal_id in ("AI-001", "AI-002")
    ]
    review_path, catalog_path = paths(tmp_path)
    review, catalog = review_and_promote(
        tmp_path / "project.json",
        write_proposal(tmp_path),
        write_decision(tmp_path, rejected),
        review_path,
        catalog_path,
        tmp_path,
    )
    assert review.status == "REVIEWED_NO_PROMOTION"
    assert review.accepted == 0
    assert review.rejected == 2
    assert catalog.scenarios == []


def test_review_requires_exact_token_and_complete_unique_decisions(tmp_path: Path) -> None:
    proposal_path = write_proposal(tmp_path)
    review_path, catalog_path = paths(tmp_path)
    with pytest.raises(ValueError, match="approval"):
        review_and_promote(
            tmp_path / "project.json",
            proposal_path,
            write_decision(tmp_path, approval="APPROVED"),
            review_path,
            catalog_path,
            tmp_path,
        )
    incomplete = [{"proposal_id": "AI-001", "decision": "ACCEPT", "rationale": "Relevant case"}]
    with pytest.raises(ValueError, match="exactly every"):
        review_and_promote(
            tmp_path / "project.json",
            proposal_path,
            write_decision(tmp_path, incomplete),
            review_path,
            catalog_path,
            tmp_path,
        )
    duplicate = [incomplete[0], incomplete[0]]
    with pytest.raises(ValueError, match="exactly one"):
        review_and_promote(
            tmp_path / "project.json",
            proposal_path,
            write_decision(tmp_path, duplicate),
            review_path,
            catalog_path,
            tmp_path,
        )


def test_blocked_proposal_and_existing_outputs_fail_closed(tmp_path: Path) -> None:
    review_path, catalog_path = paths(tmp_path)
    with pytest.raises(ValueError, match="Blocked"):
        review_and_promote(
            tmp_path / "project.json",
            write_proposal(tmp_path, blocked=True),
            write_decision(tmp_path),
            review_path,
            catalog_path,
            tmp_path,
        )
    proposal_path = write_proposal(tmp_path)
    decision_path = write_decision(tmp_path)
    review_and_promote(
        tmp_path / "project.json",
        proposal_path,
        decision_path,
        review_path,
        catalog_path,
        tmp_path,
    )
    with pytest.raises(ValueError, match="immutable"):
        review_and_promote(
            tmp_path / "project.json",
            proposal_path,
            decision_path,
            review_path,
            catalog_path,
            tmp_path,
        )


def test_review_outputs_are_confined_and_distinct(tmp_path: Path) -> None:
    proposal_path = write_proposal(tmp_path)
    decision_path = write_decision(tmp_path)
    review_path, catalog_path = paths(tmp_path)
    with pytest.raises(ValueError, match="escapes"):
        review_and_promote(
            tmp_path / "project.json",
            proposal_path,
            decision_path,
            tmp_path.parent / "record.json",
            catalog_path,
            tmp_path,
        )
    with pytest.raises(ValueError, match="distinct"):
        review_and_promote(
            tmp_path / "project.json",
            proposal_path,
            decision_path,
            review_path,
            review_path,
            tmp_path,
        )


def test_project_drift_invalidates_review(tmp_path: Path) -> None:
    proposal_path = write_proposal(tmp_path)
    decision_path = write_decision(tmp_path)
    project_path = tmp_path / "project.json"
    project = json.loads(project_path.read_text())
    project["requirements"] = ["A changed requirement"]
    project_path.write_text(json.dumps(project), encoding="utf-8")
    review_path, catalog_path = paths(tmp_path)
    with pytest.raises(ValueError, match="input hash"):
        review_and_promote(
            project_path,
            proposal_path,
            decision_path,
            review_path,
            catalog_path,
            tmp_path,
        )


def test_cli_records_human_promotion(tmp_path: Path, monkeypatch, capsys) -> None:
    proposal_path = write_proposal(tmp_path)
    decision_path = write_decision(tmp_path)
    review_path, catalog_path = paths(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "specvora",
            "review-ai",
            str(tmp_path / "project.json"),
            str(proposal_path),
            str(decision_path),
            "--workspace-root",
            str(tmp_path),
            "--review-record",
            str(review_path),
            "--promotion-catalog",
            str(catalog_path),
        ],
    )
    main()
    output = json.loads(capsys.readouterr().out)
    assert output["review"]["status"] == "PROMOTED"
    assert output["promotion"]["authority"] == "human-approved"
