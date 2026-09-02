# Module 12 — Playwright Evidence and Release Confidence

## Objective

Convert a confined Playwright JSON report into hashed, explainable evidence and feed its
normalized result into the existing deterministic confidence and audit pipeline.

## Supported report contract

The normalizer follows Playwright's JSON reporter structure: nested `suites`, `specs`,
project tests, per-test `status`, and aggregate `stats`. The source contract is documented
by the [official Playwright JSON reporter](https://playwright.dev/docs/test-reporters#json-reporter).

Statuses are interpreted conservatively:

- `expected`: passed;
- `unexpected`: failed;
- `flaky`: failed for confidence purposes and also reported separately;
- `skipped`: collected but excluded from the executed pass rate.

Treating flaky as passed could produce release confidence from an unstable signal. The
raw report remains available if a customer later adopts a different explicit policy.

## Fail-closed validation

Normalization rejects:

- reports outside the workspace or larger than 5 MB;
- invalid UTF-8 JSON or an unknown root shape;
- malformed nested suites, specs, tests, or unsupported statuses;
- aggregate statistics that disagree with collected tests;
- reports containing no executed pass/fail result.

Top-level runner or configuration errors are normalized as critical failures even when
individual test statuses appear successful. This prevents infrastructure failure from
producing a release recommendation.

## Evidence and decision flow

The evidence records the source path, SHA-256 digest, counts, failed identifiers,
critical-failure matches, normalization time, and a shared `TestRunResult`.

`Playwright JSON -> validated evidence -> TestRunResult -> confidence assessment -> hash-chained audit`

The confidence output remains a deterministic recommendation. It does not authorize a
release and does not replace accountable human judgment.

## CLI

`specvora ingest-playwright` writes evidence inside the workspace, calculates release
confidence, and appends the assessment to the existing tamper-evident audit chain.
