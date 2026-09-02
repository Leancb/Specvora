# Training Lab — Playwright Evidence and Release Confidence

## Goal

Trace a browser result from raw report to evidence, confidence, and audit without confusing
a recommendation with release authority.

## Lab

Run the provided successful example:

```powershell
specvora ingest-playwright examples\playwright_report.json `
  --workspace-root . `
  --project-id web-demo `
  --run-id web-evidence-001 `
  --requirements-total 1 `
  --requirements-covered 1 `
  --evidence-out workspaces\web-demo\runs\playwright-evidence.json `
  --audit-log workspaces\web-demo\runs\audit.jsonl
```

Then:

1. Compare the raw report SHA-256 with the evidence record.
2. Confirm the evidence source is `playwright-json-reporter`.
3. Change the test status to `flaky` and update aggregate stats.
4. Confirm flaky is visible and reduces the deterministic confidence score.
5. Add a matching `--critical-marker`; confirm the decision becomes `BLOCK`.
6. Make aggregate stats disagree with the test and confirm normalization fails closed.
7. Restore the report and verify the audit chain with `specvora verify-audit`.

## Review questions

- Why is a flaky browser test counted as a confidence failure?
- Why hash the raw report rather than only the normalized result?
- Who owns the final release decision after Specvora recommends `RELEASE`?
