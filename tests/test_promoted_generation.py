import json
import runpy
import sys
from datetime import UTC, datetime

import httpx
import pytest

from specvora.ai_proposals import AIProposalEnvelope, AIProposedScenario, proposal_input_sha256
from specvora.cli import main
from specvora.promoted_generation import _render, generate_promoted
from specvora.proposal_review import review_and_promote


def fixtures(root, status=400):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Pets", "version": "1"},
        "paths": {
            "/pets/{id}": {
                "get": {
                    "operationId": "getPet",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "integer", "minimum": 1},
                        },
                    ],
                    "responses": {
                        "200": {"description": "ok"},
                        "400": {"description": "bad input"},
                        "429": {"description": "rate limit"},
                    },
                }
            }
        },
    }
    (root / "openapi.json").write_text(json.dumps(spec))
    project = root / "project.json"
    project.write_text(
        json.dumps(
            {
                "project_id": "promoted-demo",
                "requirements": ["Read pet"],
                "openapi_path": "openapi.json",
                "base_url": "http://localhost:8080",
                "allowed_hosts": ["localhost"],
            }
        )
    )
    proposal = root / "proposal.json"
    proposal.write_text(
        AIProposalEnvelope(
            model="test-model",
            input_sha256=proposal_input_sha256(project),
            created_at=datetime.now(UTC),
            status="READY_FOR_HUMAN_REVIEW",
            findings=[],
            proposals=[
                AIProposedScenario(
                    proposal_id="AI-001",
                    requirement="Read pet",
                    operation_id="getPet",
                    kind="positive",
                    title="Read pet",
                    rationale="Positive case",
                    expected_statuses=[200],
                ),
                AIProposedScenario(
                    proposal_id="AI-002",
                    requirement="Read pet",
                    operation_id="getPet",
                    kind="negative",
                    title="Missing input",
                    rationale="Negative case",
                    expected_statuses=[status],
                ),
            ],
        ).model_dump_json()
    )
    decision = root / "decision.json"
    decision.write_text(
        json.dumps(
            {
                "reviewer": "Human reviewer",
                "approval": "APPROVED_PROPOSAL_PROMOTION",
                "decisions": [
                    {
                        "proposal_id": "AI-001",
                        "decision": "ACCEPT",
                        "rationale": "Reviewed positive",
                    },
                    {
                        "proposal_id": "AI-002",
                        "decision": "ACCEPT",
                        "rationale": "Reviewed negative",
                    },
                ],
            }
        )
    )
    review, catalog, bindings = root / "review.json", root / "catalog.json", root / "bindings.json"
    review_and_promote(project, proposal, decision, review, catalog, root)
    bindings.write_text(
        json.dumps(
            {
                "bindings": [
                    {"scenario_id": "PROM-AI-001", "case_id": "getPet-valid"},
                    {"scenario_id": "PROM-AI-002", "case_id": "getPet-missing-limit"},
                ]
            }
        )
    )
    return [project, proposal, decision, review, catalog, bindings, root / "generated", root]


def enable_fixture(args, status, value):
    spec_path = args[7] / "openapi.json"
    spec = json.loads(spec_path.read_text())
    operation = spec["paths"]["/pets/{id}"]["get"]
    operation["x-specvora-test-fixtures"] = {
        str(status): {
            "kind": "request-header",
            "name": "X-Specvora-Fixture",
            "value": value,
        }
    }
    spec_path.write_text(json.dumps(spec))
    bindings = json.loads(args[5].read_text())
    bindings["bindings"][1]["case_id"] = "getPet-valid"
    args[5].write_text(json.dumps(bindings))


def test_generates_real_parameterized_cases_without_network(tmp_path, monkeypatch):
    args = fixtures(tmp_path)
    result = generate_promoted(*args)
    assert result["status"] == "READY_FOR_HUMAN_APPROVAL"
    assert result["tests_generated"] == 2
    module = runpy.run_path(str(args[6] / "test_generated_api.py"))
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        assert "{" not in url
        assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False
        return httpx.Response(200 if "limit" in kwargs["params"] else 400)

    monkeypatch.setattr(httpx, "request", fake_request)
    monkeypatch.setenv("SPECVORA_BASE_URL", "http://localhost:8080")
    for case in module["CASES"]:
        module["test_promoted_scenario"](case)
    assert len(calls) == 2
    trace = json.loads((args[6] / "traceability.json").read_text())
    assert trace[1]["proposal_id"] == "AI-002"
    assert trace[1]["case_id"] == "getPet-missing-limit"
    with pytest.raises(FileExistsError):
        generate_promoted(*args)


@pytest.mark.parametrize("name", ["proposal", "decision", "review", "catalog"])
def test_tampered_provenance_rejected(tmp_path, name):
    args = fixtures(tmp_path)
    path = tmp_path / f"{name}.json"
    content = json.loads(path.read_text())
    if name in {"proposal", "decision"}:
        path.write_text(path.read_text() + " ")
    elif name == "review":
        content["accepted"] = 20
        path.write_text(json.dumps(content))
    else:
        content["scenarios"][0]["expected_statuses"] = [201]
        path.write_text(json.dumps(content))
    with pytest.raises(ValueError):
        generate_promoted(*args)
    assert not args[6].exists()


def test_rate_limit_requires_fixture_not_fabricated_test(tmp_path):
    args = fixtures(tmp_path, status=429)
    result = generate_promoted(*args)
    assert result["status"] == "BLOCKED"
    assert "FIXTURE_REQUIRED" in result["findings"][0]["message"]
    assert not (args[6] / "test_generated_api.py").exists()


def test_declared_fixture_generates_valid_baseline_and_header(tmp_path, monkeypatch):
    args = fixtures(tmp_path, status=429)
    enable_fixture(args, 429, "rate-limit")
    result = generate_promoted(*args)
    assert result["status"] == "READY_FOR_HUMAN_APPROVAL"
    case = json.loads((args[6] / "request-cases.json").read_text())[1]
    assert case["case_id"] == "getPet-valid"
    assert case["headers"] == {"X-Specvora-Fixture": "rate-limit"}

    module = runpy.run_path(str(args[6] / "test_generated_api.py"))

    def fake_request(method, url, **kwargs):
        return httpx.Response(200 if not kwargs["headers"] else 429)

    monkeypatch.setattr(httpx, "request", fake_request)
    monkeypatch.setenv("SPECVORA_BASE_URL", "http://localhost:8080")
    for generated_case in module["CASES"]:
        module["test_promoted_scenario"](generated_case)
    assert module["CASES"][1]["headers"] == {"X-Specvora-Fixture": "rate-limit"}


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        ({"kind": "request-header", "name": "Authorization", "value": "bad"}, "dedicated"),
        ({"kind": "request-header", "name": "X-Specvora-Fixture", "value": "../bad"}, "unsafe"),
    ],
)
def test_unsafe_fixture_definition_blocks(tmp_path, fixture, message):
    args = fixtures(tmp_path, status=429)
    spec_path = tmp_path / "openapi.json"
    spec = json.loads(spec_path.read_text())
    spec["paths"]["/pets/{id}"]["get"]["x-specvora-test-fixtures"] = {"429": fixture}
    spec_path.write_text(json.dumps(spec))
    result = generate_promoted(*args)
    assert message in result["findings"][0]["message"]


def test_missing_binding_lists_available_cases(tmp_path):
    args = fixtures(tmp_path)
    args[5].write_text('{"bindings":[]}')
    result = generate_promoted(*args)
    assert result["status"] == "BLOCKED"
    plan = json.loads((args[6] / "promotion-plan.json").read_text())
    assert any(case["case_id"] == "getPet-valid" for case in plan["available_cases"])


def test_invalid_negative_binding_blocks_generation(tmp_path):
    args = fixtures(tmp_path)
    args[5].write_text(args[5].read_text().replace("getPet-missing-limit", "getPet-valid"))
    result = generate_promoted(*args)
    assert "INEFFECTIVE_NEGATIVE" in result["findings"][0]["message"]


@pytest.mark.parametrize("duplicate", [False, True])
def test_invalid_binding_identity_rejected(tmp_path, duplicate):
    args = fixtures(tmp_path)
    data = json.loads(args[5].read_text())
    if duplicate:
        data["bindings"].append(data["bindings"][0])
    else:
        data["bindings"][0]["scenario_id"] = "not-promoted"
    args[5].write_text(json.dumps(data))
    with pytest.raises(ValueError, match=r"Duplicate|outside"):
        generate_promoted(*args)
    assert not args[6].exists()


def test_render_keeps_json_values_and_code_like_text_as_data(tmp_path, monkeypatch):
    case = {
        "scenario_id": "safe",
        "method": "POST",
        "path": "/pets",
        "params": {},
        "body": {"active": True, "other": None, "name": "'); raise RuntimeError('bad"},
        "send_json": True,
        "expected": [201],
    }
    generated = tmp_path / "generated.py"
    generated.write_text(_render([case]))
    module = runpy.run_path(str(generated))
    assert module["CASES"] == [case]

    def fake_request(method, url, **kwargs):
        assert method == "POST"
        assert kwargs["json"] == case["body"]
        return httpx.Response(201)

    monkeypatch.setattr(httpx, "request", fake_request)
    monkeypatch.setenv("SPECVORA_BASE_URL", "http://localhost:8080")
    module["test_promoted_scenario"](case)


def test_cli_and_confinement(tmp_path, monkeypatch, capsys):
    args = fixtures(tmp_path)
    outside = args.copy()
    outside[6] = tmp_path.parent / "outside-generated"
    with pytest.raises(ValueError, match="escapes"):
        generate_promoted(*outside)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "specvora",
            "generate-promoted",
            str(args[0]),
            "--proposal",
            str(args[1]),
            "--decision",
            str(args[2]),
            "--review",
            str(args[3]),
            "--catalog",
            str(args[4]),
            "--bindings",
            str(args[5]),
            "--output-dir",
            str(args[6]),
            "--workspace-root",
            str(tmp_path),
        ],
    )
    main()
    assert json.loads(capsys.readouterr().out)["tests_generated"] == 2
