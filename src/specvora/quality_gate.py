from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from specvora.case_validation import OperationValidation


class QualityGateDecision(BaseModel):
    status: Literal["READY_FOR_HUMAN_APPROVAL", "BLOCKED"]
    operations_checked: int
    cases_checked: int
    error_count: int
    blocking_codes: list[str]
    reasons: list[str]


def evaluate_generation_gate(
    validations: list[OperationValidation],
) -> QualityGateDecision:
    findings = [finding for validation in validations for finding in validation.findings]
    errors = [finding for finding in findings if finding.severity == "error"]
    blocking_codes = sorted({finding.code for finding in errors})
    if errors:
        status = "BLOCKED"
        reasons = [
            f"{len(errors)} schema validation error(s) must be resolved before approval",
            *[f"{code}: {sum(error.code == code for error in errors)}" for code in blocking_codes],
        ]
    else:
        status = "READY_FOR_HUMAN_APPROVAL"
        reasons = [
            "Generated request cases passed deterministic schema validation",
            "Human review and explicit approval are still required",
        ]
    return QualityGateDecision(
        status=status,
        operations_checked=len(validations),
        cases_checked=sum(validation.cases_checked for validation in validations),
        error_count=len(errors),
        blocking_codes=blocking_codes,
        reasons=reasons,
    )
