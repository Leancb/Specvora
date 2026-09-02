from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TestRunResult(BaseModel):
    project_id: str
    run_id: str
    total: int = Field(gt=0)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    critical_failures: int = Field(default=0, ge=0)
    requirements_total: int = Field(gt=0)
    requirements_covered: int = Field(ge=0)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_totals(self) -> TestRunResult:
        if self.passed + self.failed != self.total:
            raise ValueError("passed plus failed must equal total")
        if self.critical_failures > self.failed:
            raise ValueError("critical failures cannot exceed failed tests")
        if self.requirements_covered > self.requirements_total:
            raise ValueError("covered requirements cannot exceed total requirements")
        return self


class ConfidencePolicy(BaseModel):
    release_threshold: int = Field(default=90, ge=0, le=100)
    review_threshold: int = Field(default=70, ge=0, le=100)
    test_weight: int = Field(default=70, ge=0, le=100)
    traceability_weight: int = Field(default=30, ge=0, le=100)

    @model_validator(mode="after")
    def validate_policy(self) -> ConfidencePolicy:
        if self.review_threshold > self.release_threshold:
            raise ValueError("review threshold cannot exceed release threshold")
        if self.test_weight + self.traceability_weight != 100:
            raise ValueError("confidence weights must total 100")
        return self


class ConfidenceAssessment(BaseModel):
    project_id: str
    run_id: str
    score: int
    decision: Literal["RELEASE", "HUMAN_REVIEW", "BLOCK"]
    reasons: list[str]
    test_pass_rate: float
    traceability_rate: float
    assessed_at: datetime


def assess_release(
    result: TestRunResult, policy: ConfidencePolicy | None = None
) -> ConfidenceAssessment:
    active_policy = policy or ConfidencePolicy()
    pass_rate = result.passed / result.total
    traceability_rate = result.requirements_covered / result.requirements_total
    score = round(
        pass_rate * active_policy.test_weight
        + traceability_rate * active_policy.traceability_weight
    )
    reasons = [
        f"Test pass rate: {pass_rate:.1%}",
        f"Requirement coverage: {traceability_rate:.1%}",
    ]
    if result.critical_failures:
        decision = "BLOCK"
        reasons.append(f"Critical failures: {result.critical_failures}")
    elif score >= active_policy.release_threshold:
        decision = "RELEASE"
        reasons.append("Deterministic release threshold met")
    elif score >= active_policy.review_threshold:
        decision = "HUMAN_REVIEW"
        reasons.append("Human release decision required")
    else:
        decision = "BLOCK"
        reasons.append("Minimum confidence threshold not met")
    return ConfidenceAssessment(
        project_id=result.project_id,
        run_id=result.run_id,
        score=score,
        decision=decision,
        reasons=reasons,
        test_pass_rate=pass_rate,
        traceability_rate=traceability_rate,
        assessed_at=datetime.now(UTC),
    )
