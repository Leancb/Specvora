# Module 41 — Independently approved OIDC trust changes

Module 41 separates discovery, approval and application of identity trust.

## Governed lifecycle

1. An operator discovers and validates provider metadata and writes a new immutable proposal.
2. The proposal binds project, issuer, intended trust-file path, bootstrap/rotation mode, key IDs,
   the complete public JWKS and its SHA-256 digest.
3. A different person reviews the proposal and signs its exact bytes offline with Ed25519 for
   purpose `oidc-trust-change` and a short validity window.
4. An applying operator supplies only the signed envelope and trusted public verification key.
5. Specvora revalidates current state and key overlap, rejects self-approval, consumes the
   approval once, replaces the JWKS atomically and appends a hash-chained audit record.

The audit stores reviewer, operator, approval ID, issuer, key IDs, old/new hashes and time. It
does not store private keys, client secrets or tokens. A broken audit chain blocks later changes.

There is an unavoidable file-system transaction boundary between approval consumption, trust-file
replacement and audit append. Production deployment should place these operations in an operated
transactional change service with independent access control and durable monitoring.
