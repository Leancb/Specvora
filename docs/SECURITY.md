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

Module 23 adds the `github-ref` ledger backend for hosted CI. It verifies the approval before
atomically creating `refs/tags/specvora-approvals/<approval-id>` and starts the subprocess only
after the claim succeeds. Protect that tag namespace against deletion. The CI token has
`contents: write` only because GitHub requires it to create a reference; checkout credentials are
not persisted and the token is filtered out of the generated-test environment.

Module 24 adds signed HttpOnly portal sessions, CSRF validation and explicit viewer/reviewer/
operator capabilities. User deactivation or `session_version` changes revoke individual
sessions; rotating the external 32-byte session key revokes all sessions. Authentication never
substitutes for a purpose-bound Ed25519 approval.

Module 25 fixture adapters use dedicated headers with enumerated non-secret values. They are
test controls for isolated non-production targets, not authentication credentials or evidence
of real provider behavior. Production services must never honor these headers. Ambiguous
adapters and authenticated operations without an explicit adapter are rejected.

Module 26 adds alias-only bearer credential references. The value is resolved from the operator
process after request validation, passed only to the approved child process and redacted exactly
from captured output. Because approved generated code can read it, artifact review, signature
binding, least privilege, short lifetime and non-production scope remain mandatory. The local
environment provider is not a production secret manager.

Module 27 adds opt-in per-user TOTP and rejects reuse of the last successful counter. Enrollment
revokes older sessions and keeps the seed out of console output, but the local user file necessarily
contains sensitive TOTP seeds. There is no cross-process replay transaction, recovery workflow,
rate limiting, external federation or phishing-resistant factor; do not expose this local design as
a production identity service.

Module 28 registers signed-cookie identifiers and MFA counters in SQLite. Logout becomes a durable
server-side revocation and a conditional transactional claim prevents concurrent reuse of a TOTP
counter on one host. SQLite is not the promised multi-node store; network filesystems, replication,
retention, centralized availability and transport security remain outside this local boundary.

Module 29 introduces a persistence protocol and explicit backend selection. Unsupported or
incomplete configurations fail closed. This abstraction provides no distributed guarantee by
itself; every centralized implementation must independently prove atomicity and revocation.

Module 30 adds an HTTPS-only client for that centralized contract. Service credentials are sent
only in an Authorization header, redirects and ambient proxy settings are disabled, and network or
schema failures fail closed. The remote service itself is not included or independently verified.

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
- Secret leakage: local environment files and generated workspaces are ignored by Git; CI ledger
  tokens are not passed to generated test subprocesses.
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
The local JSON identity store is not a production identity provider. Do not expose the portal on
an untrusted network without required mode, HTTPS, secure cookies, rate limiting, MFA and an
operational identity lifecycle.
The central state service bearer is a local integration credential, not workload identity. Its
SQLite backend preserves atomicity on one host only; production requires TLS, tenant isolation,
managed rotation, availability controls and an operated transactional datastore.
The optional state-service trust file stores only time-bounded SHA-256 digests and supports
overlap during rotation. Protect its integrity and distribution; it does not provide managed
identity, revocation telemetry or proof of which workload used a bearer.
