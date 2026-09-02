from specvora.case_validation import OperationValidation, ValidationFinding
from specvora.quality_gate import evaluate_generation_gate


def test_gate_allows_progression_to_human_review_without_errors() -> None:
    decision = evaluate_generation_gate(
        [OperationValidation(operation_id="createUser", cases_checked=3, valid=True, findings=[])]
    )
    assert decision.status == "READY_FOR_HUMAN_APPROVAL"
    assert decision.error_count == 0
    assert "Human review" in decision.reasons[-1]


def test_gate_blocks_and_summarizes_deterministic_errors() -> None:
    findings = [
        ValidationFinding(
            case_id="case-1", severity="error", code="UNION_OVERLAP", message="overlap"
        ),
        ValidationFinding(
            case_id="case-2", severity="error", code="INEFFECTIVE_NEGATIVE", message="accepted"
        ),
        ValidationFinding(
            case_id="case-3", severity="error", code="UNION_OVERLAP", message="overlap"
        ),
    ]
    decision = evaluate_generation_gate(
        [
            OperationValidation(
                operation_id="createUser", cases_checked=3, valid=False, findings=findings
            )
        ]
    )
    assert decision.status == "BLOCKED"
    assert decision.error_count == 3
    assert decision.blocking_codes == ["INEFFECTIVE_NEGATIVE", "UNION_OVERLAP"]
    assert "UNION_OVERLAP: 2" in decision.reasons
