# Training Lab — From Pytest Results to Release Evidence

## Goal

Understand how raw execution output becomes confined, normalized, explainable release evidence.

## Lab

1. Produce a disposable Pytest JSON report with one passed, one failed, and one skipped test.
2. Ingest it with workspace, requirement counts, and a critical marker.
3. Inspect the normalized evidence and original report SHA-256.
4. Verify the audit chain.
5. Change a summary count without changing the tests and confirm rejection.
6. Move the report outside the workspace and confirm confinement rejection.
7. Add the critical marker to the failed node ID and predict the release decision.

## Review questions

- Why are skipped tests excluded from the executed pass rate?
- What does SHA-256 establish, and what does it not establish?
- Why must criticality come from an explicit policy rather than an AI guess?
