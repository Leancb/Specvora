import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from specvora.audit import append_assessment, verify_audit_log
from specvora.confidence import ConfidencePolicy, assess_release
from specvora.confidence import TestRunResult as RunResult


def result(**overrides: object) -> RunResult:
    values = {
        "project_id": "petstore-demo",
        "run_id": "run-001",
        "total": 10,
        "passed": 10,
        "failed": 0,
        "requirements_total": 5,
        "requirements_covered": 5,
        "executed_at": datetime(2026, 9, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return RunResult.model_validate(values)


def test_assessment_releases_only_when_threshold_is_met() -> None:
    assessment = assess_release(result())
    assert assessment.score == 100
    assert assessment.decision == "RELEASE"
    assert "threshold met" in assessment.reasons[-1]


def test_critical_failure_blocks_even_with_high_score() -> None:
    assessment = assess_release(result(passed=9, failed=1, critical_failures=1))
    assert assessment.score == 93
    assert assessment.decision == "BLOCK"


def test_intermediate_score_requires_human_review() -> None:
    assessment = assess_release(result(passed=8, failed=2, requirements_covered=4))
    assert assessment.score == 80
    assert assessment.decision == "HUMAN_REVIEW"


def test_invalid_totals_and_policy_are_rejected() -> None:
    with pytest.raises(ValidationError, match="passed plus failed"):
        result(passed=9, failed=0)
    with pytest.raises(ValidationError, match="weights must total"):
        ConfidencePolicy(test_weight=80, traceability_weight=30)


def test_audit_log_is_chained_and_detects_tampering(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    first = append_assessment(log, assess_release(result()))
    second = append_assessment(log, assess_release(result(run_id="run-002")))
    assert second["previous_hash"] == first["record_hash"]
    assert verify_audit_log(log)

    records = log.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(records[0])
    tampered["assessment"]["decision"] = "BLOCK"
    records[0] = json.dumps(tampered)
    log.write_text("\n".join(records) + "\n", encoding="utf-8")
    assert not verify_audit_log(log)
    with pytest.raises(ValueError, match="integrity"):
        append_assessment(log, assess_release(result(run_id="run-003")))
