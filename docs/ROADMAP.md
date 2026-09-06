# Roadmap

## MVP 0.1

- [x] Validate project input and OpenAPI 3 contracts.
- [x] Extract API operations and derive positive/negative scenarios.
- [x] Generate Pytest/HTTPX, traceability, quality plan, and GitHub Actions artifacts.
- [x] Enforce human approval, host allowlist, fixed commands, and workspace confinement.
- [x] Expose deterministic analysis through CLI and FastAPI.
- [x] Add execution-result audit records and deterministic release-confidence scoring.
- [x] Generate deterministic request cases from a documented JSON Schema subset.
- [x] Resolve safe internal `$ref`, basic composition, and common formats.
- [x] Normalize confined Pytest JSON reports into hashed release evidence.
- [x] Run approved local Pytest files with fixed commands, filtered environment, and timeout.
- [x] Generate visible cases for every top-level `oneOf` and `anyOf` alternative.
- [x] Validate generated cases and diagnose ineffective negatives and union overlap.
- [x] Enforce a deterministic generation gate before human approval and execution.
- [x] Generate deterministic Playwright journeys behind the same quality boundary.
- [x] Run approved Playwright journeys with fixed commands and browser request controls.
- [x] Normalize Playwright evidence and include it in release confidence and audit.
- [x] Add optional structured AI proposals with provenance and deterministic validation.
- [x] Add human review and immutable promotion for policy-valid AI proposals.
- [x] Add approved, immutable default-deny policies for container/OS network egress.
- [x] Add SQLite multi-project persistence and a local human review portal.

## Next modules

1. Add authenticated portal sessions, role authorization and key lifecycle management.
2. Add controlled fixture adapters for promoted authentication and dependency simulators.

## Module 19 checkpoint

- [x] Generate Pytest/HTTPX from promoted scenarios with explicit deterministic case bindings.
- [x] Check provenance consistency, traceability and positive/negative request validity.
- [x] Block unsupported fixtures and require separate signed execution authorization.
- [x] Portal integration and fixture-backed 429/503 test generation.

## Module 20 checkpoint

- [x] Require documented OpenAPI responses and explicit resilience fixture declarations.
- [x] Generate isolated header-driven 429/503 cases from schema-valid baselines.
- [x] Provide a local-only deterministic fixture target and safety-negative tests.
- [x] Integrate fixture selection and plan generation into the local portal.
- [x] Run controlled fixtures in an isolated, manually approved CI workflow.

## Module 21 checkpoint

- [x] List promoted scenarios and deterministic cases through confined portal APIs.
- [x] Generate new immutable plans from explicit browser selections.
- [x] Keep private signing keys and execution outside the portal boundary.
- [x] Ignore local bindings, decisions, execution sessions and ledgers in Git.
- [ ] Add authenticated sessions and roles before any non-local deployment.

## Module 22 checkpoint

- [x] Produce stable signed actions across Windows and Linux workspace roots.
- [x] Keep artifact hashes, target, allowlist and timeout inside the portable signature.
- [x] Run loopback fixtures through the signed confined runner in manual GitHub Actions.
- [x] Upload immutable evidence without placing a private key in repository or CI.
- [x] Add a durable atomic consumption ledger for cross-run replay prevention.

## Module 23 checkpoint

- [x] Validate the signed action before attempting a remote claim.
- [x] Atomically claim each approval UUID through a unique Git reference.
- [x] Keep the GitHub token outside the generated-test subprocess environment.
- [x] Preserve SQLite as the default backend for local execution.
- [ ] Add authenticated portal sessions, roles and signing-key lifecycle management.

## Module 17 checkpoint

- [x] Operator-only Ed25519 signatures, context/expiry validation and one-time consumption ledger.
- [x] Combined API/browser recommendation where the worst suite decision prevails.
- [x] Module 18: default signed authorization in portal decisions and API/browser runners.
- [ ] Authenticated sessions, revocation/rotation and production identity management.
