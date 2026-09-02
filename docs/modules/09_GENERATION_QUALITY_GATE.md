# Module 09 — Deterministic Generation Quality Gate

## Objective

Prevent invalid generated cases from reaching the execution approval boundary while preserving human authority over every runnable test.

## Decisions

- `READY_FOR_HUMAN_APPROVAL`: every generated case passed deterministic schema validation;
- `BLOCKED`: at least one error remains in the validation report.

Ready does not mean approved and does not mean safe to release. It means only that automated generation checks passed and a person may begin review.

## Blocking findings

The gate summarizes error counts and distinct codes from invalid valid cases, ineffective negative cases, union overlaps, and impossible variants. Reasons are deterministic and included in `quality-gate.json`.

## Enforcement

The controlled runner now requires all three conditions:

1. `quality-gate.json` exists and is valid JSON;
2. its status is exactly `READY_FOR_HUMAN_APPROVAL`;
3. the existing human approval and host/workspace policies pass.

A missing, malformed, or blocked gate fails closed before a process starts.

## Evidence flow

`schema -> generated cases -> validation report -> generation gate -> human review -> APPROVED -> controlled runner`

This ordering prevents human approval from bypassing a known deterministic generation defect.
