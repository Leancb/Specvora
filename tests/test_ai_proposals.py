import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from httpx import Request, Response
from openai import RateLimitError

from specvora.ai_proposals import (
    AIProposalBatch,
    AIProposalEnvelope,
    AIProposedScenario,
    _openai_provider,
    propose_scenarios,
)
from specvora.cli import main


def write_project(tmp_path: Path) -> Path:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Pets", "version": "1"},
        "paths": {
            "/pets/{petId}": {
                "get": {
                    "operationId": "getPet",
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
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


def proposal(**overrides: object) -> AIProposedScenario:
    values = {
        "proposal_id": "AI-001",
        "requirement": "Consumers can retrieve a pet",
        "operation_id": "getPet",
        "kind": "negative",
        "title": "Unsupported media type is rejected",
        "rationale": "Covers content negotiation not present in deterministic cases",
        "expected_statuses": [415],
    }
    values.update(overrides)
    return AIProposedScenario.model_validate(values)


def test_valid_proposal_is_structured_provenance_not_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SPECVORA_AI_ENABLED", "true")
    captured = {}

    def provider(prompt: str, model: str) -> AIProposalBatch:
        captured.update(prompt=prompt, model=model)
        return AIProposalBatch(proposals=[proposal()])

    output = tmp_path / "proposals/ai.json"
    result = propose_scenarios(
        write_project(tmp_path), output, tmp_path, model="test-model", provider=provider
    )
    assert result.status == "READY_FOR_HUMAN_REVIEW"
    assert result.authority == "human-review-required"
    assert result.model == "test-model"
    assert len(result.input_sha256) == 64
    assert "http://localhost" not in captured["prompt"]
    assert json.loads(output.read_text())["source"] == "openai-agents"


def test_semantic_policy_blocks_unknown_links_statuses_and_duplicates(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SPECVORA_AI_ENABLED", "true")

    def provider(prompt: str, model: str) -> AIProposalBatch:
        return AIProposalBatch(
            proposals=[
                proposal(),
                proposal(
                    requirement="Invented requirement",
                    operation_id="deleteProduction",
                    expected_statuses=[200],
                ),
            ]
        )

    result = propose_scenarios(
        write_project(tmp_path), tmp_path / "proposal.json", tmp_path, provider=provider
    )
    assert result.status == "BLOCKED"
    assert {finding.code for finding in result.findings} == {
        "DUPLICATE_PROPOSAL_ID",
        "UNKNOWN_REQUIREMENT",
        "UNKNOWN_OPERATION",
    }


def test_positive_status_must_match_documented_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SPECVORA_AI_ENABLED", "true")

    def provider(prompt: str, model: str) -> AIProposalBatch:
        return AIProposalBatch(proposals=[proposal(kind="positive", expected_statuses=[201])])

    result = propose_scenarios(
        write_project(tmp_path), tmp_path / "proposal.json", tmp_path, provider=provider
    )
    assert result.status == "BLOCKED"
    assert result.findings[0].code == "INVALID_EXPECTED_STATUS"


def test_ai_is_opt_in_and_output_is_confined(tmp_path: Path, monkeypatch) -> None:
    project = write_project(tmp_path)
    monkeypatch.delenv("SPECVORA_AI_ENABLED", raising=False)
    with pytest.raises(ValueError, match="AI_ENABLED"):
        propose_scenarios(project, tmp_path / "proposal.json", tmp_path)
    monkeypatch.setenv("SPECVORA_AI_ENABLED", "true")

    def provider(prompt: str, model: str) -> AIProposalBatch:
        return AIProposalBatch(proposals=[proposal()])

    with pytest.raises(ValueError, match="escapes"):
        propose_scenarios(project, tmp_path.parent / "proposal.json", tmp_path, provider=provider)
    with pytest.raises(ValueError, match="JSON file"):
        propose_scenarios(project, tmp_path / "proposal.py", tmp_path, provider=provider)


def test_cli_exposes_proposal_as_human_review_only(tmp_path: Path, monkeypatch, capsys) -> None:
    project = write_project(tmp_path)
    output = tmp_path / "proposals/ai.json"

    def fake_propose(*args, **kwargs) -> AIProposalEnvelope:
        return AIProposalEnvelope(
            model="test-model",
            input_sha256="0" * 64,
            created_at=datetime(2026, 9, 3, tzinfo=UTC),
            status="READY_FOR_HUMAN_REVIEW",
            findings=[],
            proposals=[proposal()],
        )

    monkeypatch.setattr("specvora.cli.propose_scenarios", fake_propose)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "specvora",
            "propose-ai",
            str(project),
            "--workspace-root",
            str(tmp_path),
            "--output",
            str(output),
            "--model",
            "test-model",
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["authority"] == "human-review-required"
    assert payload["status"] == "READY_FOR_HUMAN_REVIEW"


def test_provider_reports_exhausted_credits_without_retry(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    response = Response(429, request=Request("POST", "https://api.openai.com/v1/responses"))

    def exhausted(*args, **kwargs):
        raise RateLimitError(
            "no credits",
            response=response,
            body={"code": "credit_balance_exhausted"},
        )

    monkeypatch.setattr("agents.Runner.run_sync", exhausted)
    with pytest.raises(ValueError, match="credits are exhausted"):
        _openai_provider("proposal input", "test-model")
