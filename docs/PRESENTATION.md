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
5. API and Playwright evidence, audit, and release confidence.

## Slide 6 — Live demo: analysis

Run `specvora analyze examples\petstore_project.json`. Show the quality plan, traceability matrix, Pytest/HTTPX test, and manual GitHub Actions workflow.

## Slide 7 — Live demo: safety

Explain exact host allowlisting, explicit approval, workspace confinement, fixed command construction, and why production is not a default target.

## Slide 8 — Live demo: release confidence

Normalize the provided Pytest or Playwright report. Show its hash, the shared confidence
inputs, the score, reasons, and deterministic decision.

## Slide 9 — Audit evidence

Show the JSONL hash chain. Modify a historical decision in a disposable copy and demonstrate that `verify-audit` returns `false`.

## Slide 10 — Current evidence

Present automated tests, coverage threshold, lint, modular documentation, and Git history. State clearly which controls are implemented and which remain roadmap items.

Module 23 demo: run one signed CI approval, show its `specvora-approvals/<approval-id>` tag,
then replay the same envelope. The second run is rejected before Pytest because GitHub cannot
atomically create the same reference twice. Emphasize that the private key never enters CI.

Module 24 demo: log in with separate viewer, reviewer and operator identities. Show a rejected
role escalation and reviewer-name mismatch, then explain why login still cannot replace the
offline signature bound to the reviewed action.

Module 25 demo: generate promoted 401, 403 and 503 scenarios through declared control headers.
Remove an authentication adapter to show deterministic blocking, then explain that no real token
or dependency outage is involved and signed execution authority remains separate.

Module 26 demo: show an execution request and signed action containing only `staging-api`, inject
the hidden credential for one PowerShell process and demonstrate output redaction. Explain that
the environment provider is a local boundary awaiting managed workload identity, not a vault.

Module 27 demo: enroll one local user, show password-only rejection, complete a TOTP login and
reject immediate code reuse. Contrast local TOTP with external federation and phishing-resistant
authentication, and show that offline execution approval remains an independent authority.

Module 28 demo: copy a laboratory session, log out and show server-side rejection of the copied
cookie. Run concurrent claims for one TOTP counter and show one winner, then distinguish this
single-host SQLite transaction from a production distributed session service.

## Slide 11 — Roadmap

Demonstrate the optional AI proposal envelope: typed output, model/prompt provenance,
deterministic findings, and `human-review-required`. Then present promotion workflow,
showing complete disposition, linked hashes, and the non-executable promoted catalog.
Demonstrate the default-deny container policy, pinned endpoint, hash verification, and
privilege drop. Show the durable multi-project queue and human decision portal. Present signed
approvals and promoted-test generation as next steps.

## Slide 12 — Closing

Module 18 update: signed authorization is now the default in portal decisions and runners.
Show an approved action followed by a changed destination being rejected before subprocess launch.
Login authentication and production identity management remain pending; this is still local-only.

Module 17 demo: show a signed record failing after a one-byte change, then an API-pass/browser-
critical-failure pair producing BLOCK. Module 18 adds enforcement; the portal remains local-only.

Specvora reduces the distance from requirement to defensible release evidence while keeping ownership and authority with the customer.
