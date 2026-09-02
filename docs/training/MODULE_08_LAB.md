# Training Lab — Proving Generated Case Quality

## Goal

Distinguish case generation from case validation and interpret union diagnostics before execution.

## Lab

1. Generate cases for a required string with `minLength: 3`.
2. Inspect the valid, missing-required, and boundary values.
3. Confirm `validation-report.json` is valid and has no findings.
4. Make two `oneOf` alternatives accept the same object.
5. Run analysis and locate `UNION_OVERLAP`.
6. Change a negative value so it satisfies the schema and locate `INEFFECTIVE_NEGATIVE`.
7. Explain why none of these reports grants permission to run tests.

## Review questions

- Why is high code coverage not proof that generated data satisfies a contract?
- What is the semantic difference between `oneOf` and `anyOf`?
- Which finding should block generation from progressing to human approval?
