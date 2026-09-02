# Training Lab — Generation Quality Gate

## Goal

Understand why deterministic validation must complete before a generated test becomes eligible for human approval.

## Lab

1. Analyze a valid request schema.
2. Inspect `validation-report.json` and `quality-gate.json`.
3. Confirm the gate says `READY_FOR_HUMAN_APPROVAL`, not `APPROVED`.
4. Create overlapping `oneOf` alternatives.
5. Confirm the gate becomes `BLOCKED` and summarizes `UNION_OVERLAP`.
6. Replace the gate with malformed JSON and attempt a controlled run.
7. Restore a ready gate but omit `APPROVED`; confirm execution remains blocked.

## Review questions

- Why are generation readiness and human approval separate states?
- Which known defects should always block progression?
- Why must the runner independently re-check the persisted gate?
