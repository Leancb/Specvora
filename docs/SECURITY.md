# Security

## Trust boundaries

- Requirements, OpenAPI files, generated code, and AI output are untrusted inputs.
- Artifact generation never implies permission to execute.
- Deterministic case-validation errors block progression to human approval and execution.
- A human must provide `APPROVED` for API tests or `APPROVED_PLAYWRIGHT` for browser tests.
- The target host must exactly match an allowlisted hostname.
- Web journeys use an allowlisted base URL, relative navigation, and fixed actions only.
- Generated Playwright code cannot contain arbitrary script or `evaluate` actions.
- Browser requests outside the reviewed hostname allowlist are aborted by Playwright routing.
- Tests must remain inside the resolved workspace and use a fixed runner invocation.

## MVP threat controls

- SSRF and accidental production targeting: URL scheme validation and exact host allowlist.
- Path traversal: resolved-path confinement with `Path.is_relative_to`.
- Command injection: command arguments are constructed as a list; no generated shell text is accepted.
- Approval confusion: API and Playwright runners require distinct exact tokens.
- Review drift: the Playwright target and allowlist must match the persisted reviewed plan.
- Unreviewed AI code: deterministic mode is the default and generated files carry an approval warning.
- Secret leakage: local environment files and generated workspaces are ignored by Git.

DNS rebinding, container isolation, signed approvals, secret brokering, and operating-system
network egress enforcement remain post-MVP hardening items. Playwright routing is an
application-level defense and is not presented as a container or firewall boundary.
