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

## Next modules

1. Playwright journey generation behind the same policy boundary.
2. Optional AI proposals with schema validation and provenance.
3. Container and network egress isolation.
4. Multi-project persistence and a human review portal.
