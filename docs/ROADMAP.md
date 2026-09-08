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

## Post-MVP production roadmap

The numbered training modules are complete through Module 44. Remaining work is deployment and
service operation rather than another local training module:

1. Move portal and coordination state to an operated distributed datastore.
2. Replace runtime bearer distribution with workload identity and short-lived credentials.
3. Establish TLS/key lifecycle, backup/recovery, retention, paging ownership and measurable SLOs.
4. Add phishing-resistant user MFA and production identity-provider lifecycle operations.

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
- [x] Add authenticated portal sessions, roles and session-key lifecycle controls.

## Module 24 checkpoint

- [x] Store salted password hashes and keep the session key outside version control.
- [x] Enforce expiring HttpOnly sessions and CSRF tokens in required mode.
- [x] Separate viewer, reviewer and operator capabilities.
- [x] Bind the decision reviewer to the authenticated display name.
- [x] Support per-user and global session revocation without weakening offline approvals.
- [x] Add transactional login rate limiting.
- [ ] Add external identity federation and phishing-resistant MFA before production exposure.

## Module 25 checkpoint

- [x] Add explicit promoted adapters for authentication and dependency failures.
- [x] Restrict adapters to dedicated headers and enumerated non-secret control values.
- [x] Reject authenticated operations without an adapter and ambiguous adapter declarations.
- [x] Keep timeout simulation deterministic and preserve the legacy resilience adapter.
- [x] Preserve separate signed execution, allowlist, confinement and evidence boundaries.

## Module 26 checkpoint

- [x] Bind an alias-only credential reference into signed API execution actions.
- [x] Resolve bearer values from an operator-controlled runtime provider without persistence.
- [x] Filter the child environment and redact the exact value from captured output.
- [x] Fail closed on unavailable or structurally unsafe credential values.
- [x] Provide a hidden-prompt PowerShell workflow scoped to the current process.
- [ ] Replace the environment provider with managed workload identity before production use.

## Module 27 checkpoint

- [x] Add explicit per-user TOTP enrollment with session revocation.
- [x] Require MFA on login only for enrolled users.
- [x] Validate a bounded clock-skew window and reject reused counters locally.
- [x] Keep the enrollment secret out of console output and version control.
- [x] Add portal UI, operator workflow and deterministic RFC-vector tests.
- [x] Add transactional login rate limiting through the selected state backend.
- [x] Add hashed, one-use recovery codes through transactional state.
- [ ] Add external federation and transactional multi-node replay state.

## Module 28 checkpoint

- [x] Register issued portal sessions in transactional SQLite state.
- [x] Require an active server-side record during cookie verification.
- [x] Revoke the server-side session on logout.
- [x] Claim TOTP counters atomically and reject concurrent replay.
- [x] Preserve an explicit compatibility fallback for local Module 27 environments.
- [ ] Replace SQLite with a centralized datastore before multi-node production deployment.

## Module 29 checkpoint

- [x] Decouple portal authentication from the concrete SQLite state implementation.
- [x] Select the local backend explicitly and preserve database-path compatibility.
- [x] Fail closed for unknown backends and incomplete configuration.
- [ ] Implement and verify a centralized backend before multi-node deployment.

## Module 30 checkpoint

- [x] Implement an HTTPS client for the centralized portal state contract.
- [x] Require runtime service authentication and reject unsafe endpoints.
- [x] Disable redirects and ambient proxy configuration.
- [x] Validate response statuses and schemas without leaking remote details.
- [x] Implement and independently verify a loopback centralized state service.
- [ ] Deploy it with an operated datastore, TLS and workload identity.

## Module 31 checkpoint

- [x] Expose the portal state contract through a dedicated FastAPI service.
- [x] Authenticate every state mutation and lookup with a runtime bearer credential.
- [x] Preserve atomic MFA claims and revocable sessions through transactional SQLite.
- [x] Verify concurrent claims, lifecycle behavior and fail-closed configuration.
- [ ] Replace the training bearer and SQLite storage before production deployment.

## Module 32 checkpoint

- [x] Authenticate against strict, time-bounded SHA-256 trust entries.
- [x] Support overlapping validity windows for controlled credential rotation.
- [x] Keep plaintext bearers out of the trust file and failure responses.
- [x] Fail closed for malformed, oversized, unreadable or temporally invalid trust files.
- [ ] Replace bearer distribution with managed workload identity and auditable leases.

## Module 33 checkpoint

- [x] Claim a fixed login-attempt budget before password and TOTP verification.
- [x] Store only a normalized username hash in transactional throttle state.
- [x] Share the contract across SQLite, HTTPS adapter and central state service.
- [x] Clear the window only after complete successful authentication.
- [ ] Add edge/source controls, abuse telemetry and distributed production storage.

## Module 34 checkpoint

- [x] Generate high-entropy recovery codes only through an explicit operator workflow.
- [x] Persist only domain-separated digests in the transactional state backend.
- [x] Consume each recovery code exactly once and rotate the complete set.
- [x] Revoke earlier sessions after recovery while preserving generic login failures.
- [ ] Delegate production recovery to a federated identity lifecycle with audit alerts.

## Module 35 checkpoint

- [x] Record enumerated login, throttling and recovery events in transactional state.
- [x] Persist only event type, normalized subject hash and timezone-aware timestamp.
- [x] Share the event contract across SQLite, HTTPS adapter and central service.
- [x] Reject arbitrary metadata that could capture authentication secrets.
- [x] Export events incrementally to an authenticated, allowlisted HTTPS collector.
- [ ] Add workload identity, receiver monitoring, retention and alert ownership.

## Module 36 checkpoint

- [x] Export only the fixed pseudonymized event schema from read-only state.
- [x] Bind each canonical batch to a deterministic idempotency key.
- [x] Advance an atomic confined checkpoint only after collector acceptance.
- [x] Bound retries and reject redirects, ambient proxies and unsafe destinations.
- [ ] Replace runtime bearer authentication with managed workload identity.

## Module 37 checkpoint

- [x] Validate `RS256` ID tokens against an explicitly provisioned JWKS.
- [x] Bind exact issuer, audience, nonce and temporal claims.
- [x] Map external usernames only to active local identities and roles.
- [x] Ignore remote role/group claims and emit generic validation failures.
- [x] Add Authorization Code + PKCE with one-use server-side state and nonce.

## Module 38 checkpoint

- [x] Generate unpredictable state, nonce and an RFC 7636 verifier per login attempt.
- [x] Persist only a state digest and consume the server transaction atomically.
- [x] Exchange the code only with an exact allowlisted HTTPS token endpoint.
- [x] Disable redirects and ambient proxies and keep provider details out of failures.
- [x] Bind the ID token to the consumed nonce through Module 37 validation.
- [x] Wire provider-neutral browser routes to the local revocable session model.
- [ ] Provision provider registration and production storage/credentials in deployment.

## Module 39 checkpoint

- [x] Redirect login through the configured OIDC authorization endpoint.
- [x] Complete the one-use callback and issue the existing signed portal session.
- [x] Map only active local identities and locally assigned roles.
- [x] Return generic callback failures without provider details or tokens.
- [x] Keep the post-login destination fixed and fail closed on incomplete configuration.
- [x] Add provider discovery/key rotation under a pinned issuer policy.

## Module 40 checkpoint

- [x] Require discovery metadata to match the pinned issuer exactly.
- [x] Constrain every provider endpoint to HTTPS and explicit host allowlists.
- [x] Validate Authorization Code, RS256 and PKCE S256 capabilities.
- [x] Require trusted key overlap for staged rotations.
- [x] Write canonical validated JWKS atomically inside the workspace.
- [x] Require explicit operator approval for bootstrap and rotation scripts.
- [x] Add independent approval and a tamper-evident audit trail for trust changes.
- [x] Add read-only deterministic monitoring for trust changes and integrity failures.
- [x] Deliver bounded alerts through an authenticated, allowlisted HTTPS receiver.
- [ ] Replace runtime bearer delivery with workload identity and owned production SLOs.

## Module 41 checkpoint

- [x] Bind proposed public keys, issuer, project and target path in an immutable artifact.
- [x] Require a short-lived Ed25519 approval from a person other than the applying operator.
- [x] Consume every trust-change approval exactly once.
- [x] Revalidate current trust and overlap immediately before atomic replacement.
- [x] Append old/new hashes and accountable identities to a verified hash chain.
- [x] Keep private keys, client secrets and tokens outside proposal and audit artifacts.
- [ ] Move the multi-file transaction into an operated production change service.

## Module 42 checkpoint

- [x] Verify current JWKS structure and its binding to the last audit record.
- [x] Compare canonical current/discovered key sets without writing local state.
- [x] Distinguish unchanged, overlapping change and complete trust discontinuity.
- [x] Detect malformed, missing or tampered audit state and out-of-band JWKS changes.
- [x] Emit bounded reports with enumerated findings and no remote response details.
- [x] Preserve human-governed rotation; monitoring has no update authority.
- [x] Add authenticated, idempotent alert delivery without trust-update authority.
- [ ] Add production scheduling, workload identity and operational ownership.

## Module 43 checkpoint

- [x] Suppress network delivery for healthy observations.
- [x] Map review and blocking states to fixed warning/critical severities.
- [x] Derive stable idempotency keys from the condition rather than observation time.
- [x] Require runtime authentication and an exact HTTPS destination allowlist.
- [x] Bound retries and exclude receiver bodies and secrets from failures.
- [x] Keep monitoring and notification code independent from trust mutation.
- [ ] Enforce idempotency, retention, paging ownership and SLOs at the operated receiver.

## Module 44 checkpoint

- [x] Serialize named monitor cycles with an atomic, expiring SQLite lease.
- [x] Recover ownership after bounded expiry and release it on every completed failure path.
- [x] Record a fixed secret-free history with canonical report digests.
- [x] Combine read-only observation and authenticated delivery in one scheduler-safe CLI.
- [x] Require explicit intent to register a bounded, non-overlapping local scheduled task.
- [x] Keep every scheduling path independent from trust proposal, approval and application.
- [ ] Replace local leases and runtime bearers with operated distributed coordination and identity.

## Module 17 checkpoint

- [x] Operator-only Ed25519 signatures, context/expiry validation and one-time consumption ledger.
- [x] Combined API/browser recommendation where the worst suite decision prevails.
- [x] Module 18: default signed authorization in portal decisions and API/browser runners.
- [ ] Authenticated sessions, revocation/rotation and production identity management.
