# Module 19 — Promoted scenario test generation

`specvora generate-promoted` bridges reviewed intent and customer-owned Pytest/HTTPX
tests. It does not call an AI provider or execute requests.

## Contract

Inputs: project, original proposal, human decision, review record, promotion catalog,
and an explicit scenario-to-case binding JSON. All paths, including OpenAPI and output,
must resolve inside the supplied workspace. Output must be a new directory.

The generator checks original proposal/decision hashes, reconstructs accepted scenarios,
checks review consistency and revalidates the proposal against the current project.
These are consistency checks, not independent cryptographic authentication of the reviewer:
an attacker controlling every input can rewrite an internally consistent chain. Keep source
artifacts access-controlled. Module 18 remains responsible for signed runtime authorization.

Bindings use `{"bindings":[{"scenario_id":"PROM-AI-001","case_id":"getPet-valid"}]}`.
IDs must come from the actual catalog and generated plan, not this illustrative example.

## Deterministic gate

- Positive cases must satisfy parameter and body schemas.
- Negative cases must actually violate a request schema and expect documented 400/422.
- Expected statuses must be explicit OpenAPI response keys.
- Supported serialization: scalar path/query parameters with simple/form styles and JSON bodies.
- Authentication, header/cookie parameters, unsupported serialization and resilience cases
  (including 429/503) require future fixture adapters; they are blocked.
- Missing/unknown/duplicate bindings cannot silently choose an unrelated case.
- Any scenario finding blocks the entire batch; no executable Python file is emitted.

Schema validity does not prove business semantics, resource existence, or which of 400/422
the server actually returns. A human must review the binding and prepare a test target.

## Artifacts and authority

`promotion-plan.json` lists available cases, findings and source hashes.
`traceability.json` links requirement, proposal, scenario, operation, case and reviewer.
`request-cases.json` records materialized candidates (not permission to execute).
`quality-gate.json` is BLOCKED or READY_FOR_HUMAN_APPROVAL; ready is written last.
Only a ready batch includes `test_generated_api.py`, using a fixed template, JSON data,
timeouts, disabled redirects and disabled environment proxy inheritance.

Use the existing signed `run-pytest` workflow for execution with a fresh artifact-bound
authorization, host allowlist and confined paths. Do not run the generated file directly
as a substitute for those controls. Local processes are not hostile-code sandboxes;
network/container isolation remains a separate deployment responsibility.

No new portal button, GitHub Actions execution job or Playwright generation path is added.
Existing deterministic CI artifacts remain unchanged. Promotion is not release approval.
