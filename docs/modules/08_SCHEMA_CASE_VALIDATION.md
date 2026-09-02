# Module 08 — Schema Case Validation and Union Diagnostics

## Objective

Prove that generated positive cases satisfy the declared JSON Schema and that negative cases are actually rejected before any test code is approved or executed.

## Validation rules

- valid cases must produce no JSON Schema errors;
- missing-required and boundary cases must produce at least one error;
- a `oneOf` value must match exactly one alternative;
- an `anyOf` value must match one or more alternatives;
- format validation is enabled for supported formats;
- operations without request bodies produce an empty valid report.

## Findings

- `INVALID_VALID_CASE`: a proposed valid case violates its schema;
- `INEFFECTIVE_NEGATIVE`: a proposed negative case is still accepted;
- `UNION_OVERLAP`: a value matches multiple `oneOf` alternatives;
- `IMPOSSIBLE_VARIANT`: a generated value matches no union alternative.

Every finding includes the case ID, severity, code, and deterministic message. Any error makes the operation validation invalid.

## Generated evidence

Each analysis now writes `validation-report.json` beside `request-cases.json`. The report is reviewable and belongs to the customer. It does not authorize execution.

## Design decision

`jsonschema` is a direct runtime dependency because schema validation is part of the deterministic product boundary, not a development-only test helper.

## Demonstration

1. Analyze a normal request schema and show a clean validation report.
2. Create two identical `oneOf` alternatives.
3. Analyze again and show `UNION_OVERLAP` plus `INVALID_VALID_CASE`.
4. Explain why Specvora reports the defect instead of silently choosing an alternative.
