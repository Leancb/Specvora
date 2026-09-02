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

## Next modules

1. Controlled local runner with timeout, environment allowlist, and normalized report output.
2. Generate cases for every compatible union variant and add more constraints.
3. Playwright journey generation behind the same policy boundary.
4. Optional AI proposals with schema validation and provenance.
5. Container and network egress isolation.
6. Multi-project persistence and a human review portal.
