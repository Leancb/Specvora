# Security

## Trust boundaries

- Requirements, OpenAPI files, generated code, and AI output are untrusted inputs.
- Artifact generation never implies permission to execute.
- A human must provide the exact `APPROVED` decision at execution time.
- The target host must exactly match an allowlisted hostname.
- Tests must remain inside the resolved workspace and use a fixed Pytest invocation.

## MVP threat controls

- SSRF and accidental production targeting: URL scheme validation and exact host allowlist.
- Path traversal: resolved-path confinement with `Path.is_relative_to`.
- Command injection: command arguments are constructed as a list; no generated shell text is accepted.
- Unreviewed AI code: deterministic mode is the default and generated files carry an approval warning.
- Secret leakage: local environment files and generated workspaces are ignored by Git.

DNS rebinding, container isolation, signed approvals, secret brokering, and network egress enforcement remain post-MVP hardening items.
