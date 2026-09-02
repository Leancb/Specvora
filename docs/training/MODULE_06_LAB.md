# Training Lab — Controlled Test Execution

## Goal

Trace every authorization and confinement decision from a generated test file to audited release evidence.

## Lab

1. Review the generated test before approving it.
2. Start a disposable local API target on an allowlisted host.
3. Run `specvora run-pytest` with `APPROVED`.
4. Inspect process output, JSON report, normalized evidence, assessment, and audit record.
5. Replace approval with another value and confirm rejection.
6. Replace the base URL with a non-allowlisted host and confirm rejection.
7. Attempt to place the report outside the workspace and confirm rejection.
8. Use a disposable sleeping test with a one-second timeout and observe fail-closed behavior.

## Review questions

- Why is a failed test different from a runner failure?
- Why is environment inheritance a secret-leakage risk?
- Which controls are required before adding a remote execution API?
