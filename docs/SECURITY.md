# Security

Current Module 18 behavior: portal
decisions and controlled runners now require signed actions by default. Operator-selected
`local-development` mode is an explicit compatibility bypass, never a production setting.
Trust configuration is server-owned. See `modules/18_SIGNED_AUTHORIZATION_INTEGRATION.md`
for filesystem race limitations, at-most-once consumption, and remaining login/authentication work.

Module 17 adds detached Ed25519 approval verification and a shared consumption ledger for
operator workflows. Module 18 connects signature verification to portal decisions and runners;
session authentication remains unimplemented.
Never treat a public key supplied by an untrusted approval itself as trusted; enrollment is an
operator responsibility. Keep private key files outside the repository and protect ledger backups.

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
- Pytest and Playwright reports are size-limited, schema-checked, and hashed before use.
- AI is opt-in, tool-free, schema-constrained, semantically validated, and proposal-only.
- AI promotion requires complete human disposition, a dedicated token, and immutable outputs.
- Isolated egress policy creation requires a distinct approval and pins exact IPs and TCP port.
- The Linux execution image applies a default-deny `nftables` policy before dropping privileges.
- Portal project and proposal files must resolve inside their registered workspace.
- A queued proposal is revalidated before entry and the existing promotion policy handles decisions.

## MVP threat controls

- SSRF and accidental production targeting: URL scheme validation and exact host allowlist.
- Path traversal: resolved-path confinement with `Path.is_relative_to`.
- Command injection: command arguments are constructed as a list; no generated shell text is accepted.
- Approval confusion: API and Playwright runners require distinct exact tokens.
- Review drift: the Playwright target and allowlist must match the persisted reviewed plan.
- Unreviewed AI code: deterministic mode is the default and generated files carry an approval warning.
- Secret leakage: local environment files and generated workspaces are ignored by Git.
- Evidence spoofing: report summaries must agree with validated per-test outcomes.
- Prompt injection: model input is minimized, treated as data, and cannot directly invoke tools.
- AI overreach: model output cannot enter generated tests or execution without a future human workflow.
- Review tampering: proposal and decision inputs are SHA-256 bound to each promotion record.
- Approval confusion: proposal promotion uses a token distinct from API and browser execution.
- DNS rebinding during an isolated run: DNS is omitted and the reviewed hostname is pinned to
  the addresses recorded in the immutable policy.
- Direct network bypass: the container output chain drops traffic not matching the pinned target.

The application-level runners remain available for local development and are not an OS security
boundary. The isolated profile requires a Linux container runtime with network namespaces,
`nftables`, and temporary `CAP_NET_ADMIN`; deployments must not use host networking or add other
capabilities. Signed approvals and secret brokering remain post-MVP hardening items.
The current portal is intentionally local and has no authentication, authorization roles, or
CSRF protection. Do not expose it on an untrusted network; production deployment is blocked
on those controls and signed approval records.
