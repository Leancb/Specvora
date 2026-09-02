from specvora.case_validation import validate_request_cases
from specvora.data_cases import RequestCase, generate_request_cases
from specvora.models import Operation


def operation(schema: dict[str, object]) -> Operation:
    return Operation(
        operation_id="createThing",
        method="POST",
        path="/things",
        success_statuses=[201],
        request_schema=schema,
    )


def test_accepts_effective_valid_and_negative_cases() -> None:
    target = operation(
        {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string", "minLength": 3}},
        }
    )
    report = validate_request_cases(target, generate_request_cases(target))
    assert report.valid
    assert report.cases_checked == 3
    assert report.findings == []


def test_detects_overlapping_oneof_variants() -> None:
    target = operation(
        {
            "oneOf": [
                {"type": "object", "required": ["name"]},
                {"type": "object", "required": ["name"]},
            ],
            "x-specvora-union-policy": "all-variants",
        }
    )
    cases = [
        RequestCase(
            case_id="createThing-valid-oneOf-1",
            operation_id="createThing",
            kind="valid",
            body={"name": "x"},
        )
    ]
    report = validate_request_cases(target, cases)
    assert not report.valid
    assert {finding.code for finding in report.findings} == {
        "INVALID_VALID_CASE",
        "UNION_OVERLAP",
    }


def test_detects_impossible_variant_and_ineffective_negative() -> None:
    target = operation({"type": "string", "minLength": 3})
    cases = [
        RequestCase(
            case_id="invalid-valid",
            operation_id="createThing",
            kind="valid",
            body="x",
        ),
        RequestCase(
            case_id="accepted-negative",
            operation_id="createThing",
            kind="invalid_boundary",
            body="valid",
        ),
    ]
    report = validate_request_cases(target, cases)
    assert not report.valid
    assert {finding.code for finding in report.findings} == {
        "INVALID_VALID_CASE",
        "INEFFECTIVE_NEGATIVE",
    }


def test_operation_without_body_has_empty_valid_report() -> None:
    target = operation({})
    target.request_schema = None
    report = validate_request_cases(target, [])
    assert report.valid
    assert report.cases_checked == 0
