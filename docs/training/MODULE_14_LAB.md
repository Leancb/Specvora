# Training Lab — Human Proposal Review and Promotion

## Goal

Practice accountable disposition of every AI proposal and verify that promotion remains
separate from code generation and execution.

## Lab

Run the offline training fixtures:

```powershell
specvora review-ai `
  examples\petstore_project.json `
  examples\ai_proposal_example.json `
  examples\ai_review_decision.json `
  --workspace-root . `
  --review-record workspaces\petstore-demo\reviews\review-001.json `
  --promotion-catalog workspaces\petstore-demo\promoted\catalog-001.json
```

Then:

1. Compare both source files with the SHA-256 values in the outputs.
2. Confirm only `AI-001` became `PROM-AI-001`.
3. Confirm the rejected proposal and rationale remain in the review record.
4. Remove one decision and confirm the review fails closed.
5. Replace the token with `APPROVED` and confirm it is rejected.
6. Mark the proposal envelope `BLOCKED` and confirm promotion is impossible.
7. Repeat the original command and confirm immutable outputs are not overwritten.
8. Confirm no Pytest, Playwright, runner, or release-decision artifact was created.

Use new output filenames for each legitimate review attempt.

## Review questions

- Why must rejected proposals remain visible in the review record?
- What does hashing both inputs prove, and what does it not prove?
- Which additional approval is required before an accepted scenario may execute?
