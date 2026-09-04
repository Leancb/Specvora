from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from specvora.confidence import (
    ConfidenceAssessment,
    ConfidencePolicy,
    TestRunResult,
    assess_release,
)


class CombinedReleaseRequest(BaseModel):
    project_id: str = Field(min_length=1)
    release_id: str = Field(min_length=1)
    api: TestRunResult
    browser: TestRunResult
    policy: ConfidencePolicy = Field(default_factory=ConfidencePolicy)


class CombinedReleaseAssessment(BaseModel):
    project_id: str
    release_id: str
    decision: Literal["RELEASE", "HUMAN_REVIEW", "BLOCK"]
    api: ConfidenceAssessment
    browser: ConfidenceAssessment
    reasons: list[str]
    authority: Literal["recommendation-only"] = "recommendation-only"


def assess_combined(request: CombinedReleaseRequest) -> CombinedReleaseAssessment:
    if any(result.project_id != request.project_id for result in (request.api, request.browser)):
        raise ValueError("Both suites must belong to the requested project")
    if request.api.run_id == request.browser.run_id:
        raise ValueError("API and browser evidence require distinct run IDs")
    api = assess_release(request.api, request.policy)
    browser = assess_release(request.browser, request.policy)
    severity = {"RELEASE": 0, "HUMAN_REVIEW": 1, "BLOCK": 2}
    decision = max((api.decision, browser.decision), key=severity.__getitem__)
    return CombinedReleaseAssessment(
        project_id=request.project_id,
        release_id=request.release_id,
        decision=decision,
        api=api,
        browser=browser,
        reasons=[
            f"API: {api.decision}",
            f"Browser: {browser.decision}",
            "Worst suite decision prevails; scores are never averaged",
        ],
    )
