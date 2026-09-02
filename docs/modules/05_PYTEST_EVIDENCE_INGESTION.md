# Module 05 — Controlled Pytest Evidence Ingestion

## Objective

Convert a real `pytest-json-report` file into normalized, hash-identified evidence before release-confidence assessment.

## Security and validation

- the report must resolve inside the declared workspace;
- the file must exist and remain under 5 MB;
- the root, tests collection, outcomes, and optional summary are validated;
- only passed, failed, and skipped outcomes are accepted;
- summary counts must match individual tests;
- evidence output must also remain inside the workspace;
- the original report receives a SHA-256 identifier.

Skipped tests are preserved as evidence but excluded from the executed pass rate. A report with no passed or failed tests is rejected.

## Critical failures

Critical markers are supplied explicitly by a human or policy owner. A failed node ID containing a configured marker increments critical failures and therefore blocks release confidence. Specvora does not infer criticality with AI.

## CLI workflow

```powershell
specvora ingest-pytest workspaces\petstore-demo\runs\pytest-report.json `
  --workspace-root workspaces\petstore-demo `
  --project-id petstore-demo `
  --run-id demo-001 `
  --requirements-total 5 `
  --requirements-covered 5 `
  --critical-marker security `
  --evidence-out workspaces\petstore-demo\runs\evidence.json `
  --audit-log workspaces\petstore-demo\runs\audit.jsonl
```

The command normalizes evidence, calculates confidence through the existing deterministic policy, and appends the assessment to the audit chain.

## Current limitation

The MVP accepts the JSON structure produced by `pytest-json-report`; it does not run Pytest itself or trust arbitrary plugin metadata. Cryptographic signatures and external evidence anchoring remain future hardening.
