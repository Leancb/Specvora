# Specvora Presentation Script

## Slide 1 — Vision

Specvora: Autonomous Quality Engineering — from requirements to release confidence.

Speaker note: autonomous means accelerated and policy-governed, not uncontrolled.

## Slide 2 — Problem

Requirements, API contracts, automated tests, CI evidence, and release decisions often live in disconnected tools. This creates delay and weak traceability.

## Slide 3 — Product promise

Specvora converts requirements plus OpenAPI into a customer-owned quality plan, executable tests, traceability, and an explainable release recommendation.

## Slide 4 — Governance model

AI proposes. Deterministic policies validate. Humans authorize. Generated code is never authority and never receives implicit permission to run.

## Slide 5 — Modular architecture

1. Requirements and OpenAPI analysis.
2. Scenario and artifact generation.
3. Approved and confined execution policy.
4. Results, audit, and release confidence.
5. Future Playwright journeys and optional AI proposals.

## Slide 6 — Live demo: analysis

Run `specvora analyze examples\petstore_project.json`. Show the quality plan, traceability matrix, Pytest/HTTPX test, and manual GitHub Actions workflow.

## Slide 7 — Live demo: safety

Explain exact host allowlisting, explicit approval, workspace confinement, fixed command construction, and why production is not a default target.

## Slide 8 — Live demo: release confidence

Run `specvora assess examples\petstore_results.json --audit-log workspaces\petstore-demo\runs\audit.jsonl`. Show the score, reasons, and deterministic decision.

## Slide 9 — Audit evidence

Show the JSONL hash chain. Modify a historical decision in a disposable copy and demonstrate that `verify-audit` returns `false`.

## Slide 10 — Current evidence

Present automated tests, coverage threshold, lint, modular documentation, and Git history. State clearly which controls are implemented and which remain roadmap items.

## Slide 11 — Roadmap

Request-data generation from JSON Schema, real runner result ingestion, Playwright, signed approvals, container isolation, egress control, and multi-project review portal.

## Slide 12 — Closing

Specvora reduces the distance from requirement to defensible release evidence while keeping ownership and authority with the customer.
