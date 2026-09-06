"""Generate owned tests from reviewed intent and explicit deterministic case bindings."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from pydantic import BaseModel, ConfigDict

from specvora.ai_proposals import AIProposalEnvelope, validate_proposal_envelope
from specvora.data_cases import generate_request_cases
from specvora.models import ProjectInput
from specvora.openapi import extract_operations, load_openapi
from specvora.proposal_review import (
    HumanReviewInput,
    PromotionCatalog,
    ProposalReviewRecord,
    _promoted,
    _validate_decisions,
)
from specvora.schema_resolver import resolve_document


class CaseBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str
    case_id: str


class GenerationBindings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bindings: list[CaseBinding]


def _confined(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("Promoted generation path escapes the workspace")
    return resolved


def generate_promoted(
    project_file: Path,
    proposal_file: Path,
    decision_file: Path,
    review_file: Path,
    catalog_file: Path,
    bindings_file: Path,
    output_dir: Path,
    workspace_root: Path,
) -> dict:
    inputs = {
        name: _confined(path, workspace_root)
        for name, path in {
            "project": project_file,
            "proposal": proposal_file,
            "decision": decision_file,
            "review": review_file,
            "catalog": catalog_file,
            "bindings": bindings_file,
        }.items()
    }
    raw = {name: path.read_bytes() for name, path in inputs.items()}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in raw.items()}
    project = ProjectInput.model_validate_json(raw["project"])
    specification = _confined(inputs["project"].parent / project.openapi_path, workspace_root)
    hashes["openapi"] = hashlib.sha256(specification.read_bytes()).hexdigest()
    envelope = AIProposalEnvelope.model_validate_json(raw["proposal"])
    decision = HumanReviewInput.model_validate_json(raw["decision"])
    review = ProposalReviewRecord.model_validate_json(raw["review"])
    catalog = PromotionCatalog.model_validate_json(raw["catalog"])
    bindings = GenerationBindings.model_validate_json(raw["bindings"])
    _validate_chain(envelope, decision, review, catalog, hashes)
    if envelope.status != "READY_FOR_HUMAN_REVIEW" or envelope.findings:
        raise ValueError("Blocked proposal cannot enter promoted generation")
    if validate_proposal_envelope(envelope, inputs["project"]):
        raise ValueError("Proposal no longer satisfies project policy")
    document = resolve_document(load_openapi(specification))
    operations = extract_operations(document)
    by_operation = {operation.operation_id: operation for operation in operations}
    if len(by_operation) != len(operations):
        raise ValueError("Duplicate operation IDs are ambiguous")
    by_binding = {binding.scenario_id: binding.case_id for binding in bindings.bindings}
    if len(by_binding) != len(bindings.bindings):
        raise ValueError("Duplicate scenario bindings")
    scenario_ids = {scenario.scenario_id for scenario in catalog.scenarios}
    if set(by_binding) - scenario_ids:
        raise ValueError("Binding references a scenario outside the promoted catalog")
    findings, trace, executable, available = [], [], [], []
    for scenario in catalog.scenarios:
        operation = by_operation[scenario.operation_id]
        cases = generate_request_cases(operation)
        available.extend(case.model_dump(mode="json") for case in cases)
        candidate = next(
            (case for case in cases if case.case_id == by_binding.get(scenario.scenario_id)), None
        )
        row = {
            "scenario_id": scenario.scenario_id,
            "proposal_id": scenario.source_proposal_id,
            "requirement": scenario.requirement,
            "operation_id": scenario.operation_id,
            "case_id": by_binding.get(scenario.scenario_id),
            "reviewer": scenario.reviewed_by,
        }
        trace.append(row)
        try:
            operation_doc = document["paths"][operation.path][operation.method.lower()]
            raw_parameters = document["paths"][operation.path].get("parameters", [])
            raw_parameters = [*raw_parameters, *operation_doc.get("parameters", [])]
            for parameter in raw_parameters:
                default_style = "simple" if parameter.get("in") == "path" else "form"
                if "content" in parameter or parameter.get("style", default_style) != default_style:
                    raise ValueError("UNSUPPORTED_SERIALIZATION: parameter style needs an adapter")
            authenticated = bool(operation_doc.get("security", document.get("security")))
            body_doc = operation_doc.get("requestBody", {})
            if body_doc and "application/json" not in body_doc.get("content", {}):
                raise ValueError("UNSUPPORTED_SERIALIZATION: only JSON request bodies supported")
            response_codes = operation_doc["responses"]
            if any(str(status) not in response_codes for status in scenario.expected_statuses):
                raise ValueError(
                    "UNDOCUMENTED_STATUS: expected response must be explicit in OpenAPI"
                )
            fixture = _fixture_for(operation_doc, scenario.expected_statuses, authenticated)
            if (
                scenario.kind == "negative"
                and not set(scenario.expected_statuses) <= {400, 422}
                and fixture is None
            ):
                raise ValueError(
                    "FIXTURE_REQUIRED: resilience/auth/rate-limit behavior needs setup"
                )
            if candidate is None:
                raise ValueError("MISSING_CASE_BINDING: choose a deterministic case from the plan")
            request = _materialize(operation, candidate, scenario.kind, fixture is not None)
            request["headers"] = fixture or {}
            executable.append({**row, **request, "expected": scenario.expected_statuses})
        except ValueError as exc:
            findings.append({"scenario_id": scenario.scenario_id, "message": str(exc)})
    if not catalog.scenarios:
        findings.append({"scenario_id": None, "message": "EMPTY_PROMOTION: no accepted scenarios"})
    status = "BLOCKED" if findings else "READY_FOR_HUMAN_APPROVAL"
    output = _confined(output_dir, workspace_root)
    output.mkdir(parents=True, exist_ok=False)
    gate = {"status": "BLOCKED", "authority": "human-execution-approval-required"}
    _write_json(output / "quality-gate.json", gate)
    _write_json(
        output / "promotion-plan.json",
        {
            "project_id": project.project_id,
            "source_hashes": hashes,
            "available_cases": available,
            "findings": findings,
        },
    )
    _write_json(output / "traceability.json", trace)
    _write_json(output / "request-cases.json", executable)
    if status != "BLOCKED":
        (output / "test_generated_api.py").write_text(_render(executable), encoding="utf-8")
    gate.update(status=status, findings=findings, source_hashes=hashes)
    _write_json(output / "quality-gate.json", gate)
    return {
        "project_id": project.project_id,
        "status": status,
        "output_dir": str(output),
        "tests_generated": len(executable) if status != "BLOCKED" else 0,
        "findings": findings,
    }


def _validate_chain(envelope, decision, review, catalog, hashes):
    _validate_decisions(envelope, decision)
    if decision.approval != "APPROVED_PROPOSAL_PROMOTION":
        raise ValueError("Promotion approval is missing")
    for item in (review, catalog):
        if (
            item.source_proposal_sha256 != hashes["proposal"]
            or item.review_decision_sha256 != hashes["decision"]
        ):
            raise ValueError("Promotion provenance hash mismatch")
    proposals = {proposal.proposal_id: proposal for proposal in envelope.proposals}
    expected = [
        _promoted(proposals[item.proposal_id], decision.reviewer)
        for item in decision.decisions
        if item.decision == "ACCEPT"
    ]
    if catalog.scenarios != expected:
        raise ValueError("Catalog differs from the accepted proposals")
    if (
        review.decisions != decision.decisions
        or review.reviewer != decision.reviewer
        or review.accepted != len(expected)
        or review.rejected != len(decision.decisions) - len(expected)
        or review.reviewed_at != catalog.promoted_at
        or review.status != ("PROMOTED" if expected else "REVIEWED_NO_PROMOTION")
    ):
        raise ValueError("Review record differs from the human decision")


def _errors(schema, value):
    validator = validator_for(schema)
    validator.check_schema(schema)
    return list(validator(schema, format_checker=FormatChecker()).iter_errors(value))


def _fixture_for(operation_doc, expected_statuses, authenticated=False):
    if len(expected_statuses) != 1:
        return None
    status = str(expected_statuses[0])
    candidates = []
    definitions = (
        (
            "x-specvora-auth-fixtures",
            "X-Specvora-Auth-Fixture",
            {"valid", "missing", "expired", "insufficient-scope"},
        ),
        (
            "x-specvora-dependency-fixtures",
            "X-Specvora-Dependency-Fixture",
            {"unavailable", "timeout"},
        ),
        ("x-specvora-test-fixtures", "X-Specvora-Fixture", None),
    )
    for extension, header, allowed_values in definitions:
        fixture = operation_doc.get(extension, {}).get(status)
        if fixture is not None:
            candidates.append((fixture, header, allowed_values))
    if len(candidates) > 1:
        raise ValueError("INVALID_FIXTURE: multiple adapters target the same status")
    if not candidates:
        if authenticated:
            raise ValueError("FIXTURE_REQUIRED: authenticated operation needs a declared adapter")
        return None
    fixture, header, allowed_values = candidates[0]
    if fixture is None:
        return None
    if not isinstance(fixture, dict) or set(fixture) != {"kind", "name", "value"}:
        raise ValueError("INVALID_FIXTURE: expected kind, name and value only")
    if fixture["kind"] != "request-header" or fixture["name"] != header:
        raise ValueError("INVALID_FIXTURE: adapter must use its dedicated fixture header")
    if not isinstance(fixture["value"], str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]{0,63}", fixture["value"]
    ):
        raise ValueError("INVALID_FIXTURE: unsafe fixture value")
    if allowed_values is not None and fixture["value"] not in allowed_values:
        raise ValueError("INVALID_FIXTURE: unsupported adapter state")
    return {fixture["name"]: fixture["value"]}


def _materialize(operation, case, kind, fixture_backed=False):
    names = [parameter.name for parameter in operation.parameters]
    if len(names) != len(set(names)):
        raise ValueError("UNSUPPORTED_SERIALIZATION: duplicate parameter names")
    path, query, errors = operation.path, {}, []
    if not path.startswith("/") or path.startswith("//") or any(c in path for c in "?#"):
        raise ValueError("UNSAFE_PATH: expected a relative API path")
    for parameter in operation.parameters:
        if parameter.location not in {"path", "query"}:
            raise ValueError(
                "UNSUPPORTED_SERIALIZATION: only scalar path/query parameters supported"
            )
        if parameter.name not in case.parameters:
            if parameter.required:
                errors.append("missing parameter")
            if parameter.location == "path":
                raise ValueError("UNRESOLVED_PATH: missing path parameter")
            continue
        value = case.parameters[parameter.name]
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError("UNSUPPORTED_SERIALIZATION: parameter must be scalar")
        errors.extend(_errors(parameter.schema_definition, value))
        wire = str(value).lower() if isinstance(value, bool) else str(value)
        if parameter.location == "path":
            path = path.replace("{" + parameter.name + "}", quote(wire, safe=""))
        else:
            query[parameter.name] = wire
    if "{" in path or "}" in path or any(part in {".", ".."} for part in path.split("/")):
        raise ValueError("UNRESOLVED_PATH: invalid path substitution")
    if operation.request_schema is not None:
        errors.extend(_errors(operation.request_schema, case.body))
    if kind == "positive" and (case.kind != "valid" or errors):
        raise ValueError("INVALID_POSITIVE: case does not satisfy the request schema")
    if kind == "negative":
        if fixture_backed and (case.kind != "valid" or errors):
            raise ValueError("INVALID_FIXTURE_BASELINE: fixture requires a valid request case")
        if not fixture_backed and (case.kind == "valid" or not errors):
            raise ValueError("INEFFECTIVE_NEGATIVE: case does not violate the request schema")
    return {
        "method": operation.method,
        "path": path,
        "params": query,
        "body": case.body,
        "send_json": operation.request_schema is not None,
    }


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _render(cases) -> str:
    encoded = repr(json.dumps(cases, ensure_ascii=True))
    return f'''"""Generated promoted API cases. Separate signed execution approval required."""
import json
import os
import httpx
import pytest

CASES = json.loads({encoded})

@pytest.mark.parametrize("case", CASES, ids=lambda case: case["scenario_id"])
def test_promoted_scenario(case):
    headers = dict(case.get("headers", {{}}))
    if authorization := os.environ.get("SPECVORA_RUNTIME_AUTHORIZATION"):
        headers["Authorization"] = authorization
    kwargs = {{"params": case["params"], "headers": headers,
              "timeout": 10, "follow_redirects": False,
              "trust_env": False}}
    if case["send_json"]:
        kwargs["json"] = case["body"]
    response = httpx.request(case["method"], os.environ["SPECVORA_BASE_URL"].rstrip("/")
                             + case["path"], **kwargs)
    assert response.status_code in case["expected"]
'''
