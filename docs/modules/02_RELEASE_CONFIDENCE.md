# Module 02 — Results, Audit, and Release Confidence

## Objective

Convert real automated-test results into an explainable release recommendation without transferring release authority to AI.

## Inputs and outputs

Input is a validated JSON result containing counts for tests, critical failures, and covered requirements. Output contains a score from 0 to 100, a deterministic decision, reasons, and an audit entry.

## Decision policy

- `RELEASE`: score at least 90 and no critical failures.
- `HUMAN_REVIEW`: score from 70 through 89 and no critical failures.
- `BLOCK`: score below 70 or any critical failure.

The default score is 70% test pass rate plus 30% requirements coverage. Policies are explicit Pydantic models and can be reviewed, versioned, and tested.

## Audit model

Every assessment is appended to a JSONL file. Each record includes the previous record hash and its own SHA-256 hash. This makes editing, reordering, or deleting historical entries detectable. It is tamper-evident, not a substitute for signed or externally anchored audit storage.

## Demonstration

```powershell
specvora assess examples\petstore_results.json --audit-log workspaces\petstore-demo\runs\audit.jsonl
specvora verify-audit workspaces\petstore-demo\runs\audit.jsonl
```

## Acceptance evidence

- release, human-review, and block branches have deterministic tests;
- invalid totals and invalid policies are rejected;
- audit chaining and tamper detection are tested;
- CLI and API exercise the same domain service.
