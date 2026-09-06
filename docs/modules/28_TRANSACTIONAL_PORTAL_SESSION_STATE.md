# Module 28 — Transactional portal session state

Module 28 moves active-session revocation and TOTP replay counters into a dedicated SQLite state
store. `SPECVORA_PORTAL_STATE_DB` enables the store; the portal setup script configures
`.specvora-auth/session-state.db` automatically.

Every new signed cookie contains a random session identifier registered server-side with its user
and expiry. Verification requires both a valid cookie signature and an active database record.
Logout revokes that record before deleting the browser cookie, so a copied cookie cannot be used
again after logout.

TOTP counters are claimed with `BEGIN IMMEDIATE` and a conditional UPSERT. Concurrent attempts to
consume the same or an older counter result in exactly one success. This replaces the file-only
check when the transactional store is configured.

## Compatibility and limits

Without `SPECVORA_PORTAL_STATE_DB`, the Module 27 local file behavior remains available for existing
development environments. Enabling the database intentionally invalidates older cookies that have
no registered session identifier.

SQLite provides a durable transactional boundary for one host and multiple local processes. It is
not a distributed database and must not be placed on an unsupported shared network filesystem.
Production multi-node deployment still requires a centralized datastore, encrypted transport,
backup/restore policy, retention cleanup, observability and failure-mode testing.

Session state does not replace role authorization, CSRF, TOTP seed protection, offline Ed25519
approval, allowlisting, execution confinement or human release authority.
