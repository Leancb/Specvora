from __future__ import annotations

from typing import Literal

from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from pydantic import BaseModel

from specvora.data_cases import RequestCase
from specvora.models import Operation


class ValidationFinding(BaseModel):
    case_id: str
    severity: Literal["error", "warning"]
    code: Literal[
        "INVALID_VALID_CASE",
        "INEFFECTIVE_NEGATIVE",
        "UNION_OVERLAP",
        "IMPOSSIBLE_VARIANT",
    ]
    message: str


class OperationValidation(BaseModel):
    operation_id: str
    cases_checked: int
    valid: bool
    findings: list[ValidationFinding]


def validate_request_cases(operation: Operation, cases: list[RequestCase]) -> OperationValidation:
    schema = operation.request_schema
    if not schema:
        return OperationValidation(
            operation_id=operation.operation_id,
            cases_checked=0,
            valid=True,
            findings=[],
        )
    validator = _validator(schema)
    findings: list[ValidationFinding] = []
    checked = [case for case in cases if case.body is not None]
    for case in checked:
        errors = sorted(validator.iter_errors(case.body), key=lambda error: list(error.path))
        if case.kind == "valid" and errors:
            findings.append(
                ValidationFinding(
                    case_id=case.case_id,
                    severity="error",
                    code="INVALID_VALID_CASE",
                    message=errors[0].message,
                )
            )
        elif case.kind != "valid" and not errors:
            findings.append(
                ValidationFinding(
                    case_id=case.case_id,
                    severity="error",
                    code="INEFFECTIVE_NEGATIVE",
                    message="Negative case is accepted by the request schema",
                )
            )
        if case.kind == "valid":
            findings.extend(_union_findings(schema, case))
    return OperationValidation(
        operation_id=operation.operation_id,
        cases_checked=len(checked),
        valid=not any(finding.severity == "error" for finding in findings),
        findings=findings,
    )


def _union_findings(schema: dict[str, object], case: RequestCase) -> list[ValidationFinding]:
    for keyword in ("oneOf", "anyOf"):
        choices = schema.get(keyword)
        if not isinstance(choices, list):
            continue
        matches = sum(not list(_validator(choice).iter_errors(case.body)) for choice in choices)
        if matches == 0:
            return [
                ValidationFinding(
                    case_id=case.case_id,
                    severity="error",
                    code="IMPOSSIBLE_VARIANT",
                    message=f"Generated value matches no {keyword} alternative",
                )
            ]
        if keyword == "oneOf" and matches > 1:
            return [
                ValidationFinding(
                    case_id=case.case_id,
                    severity="error",
                    code="UNION_OVERLAP",
                    message=f"Generated value matches {matches} oneOf alternatives",
                )
            ]
    return []


def _validator(schema: object):
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    return validator_class(schema, format_checker=FormatChecker())
