# Module 38 — One-use OIDC Authorization Code + PKCE

This module completes the browser-facing OIDC security foundation without transferring
authorization authority to the identity provider.

## Security boundary

- Authorization Code uses `response_mode=query` and PKCE `S256`.
- Random `state`, nonce and verifier expire after five minutes.
- Only the SHA-256 digest of `state` is stored.
- Nonce and verifier stay server-side and are atomically consumed before token exchange.
- The token endpoint must be HTTPS and its exact hostname must be allowlisted.
- Redirects, ambient proxies and verbose provider errors are rejected.
- Strict RS256 validation binds issuer, audience, time and the consumed nonce.

The IdP authenticates a subject. Specvora maps it only to an active local user and local roles.
OIDC cannot approve test execution or release.

SQLite demonstrates one-host atomicity. Production still needs an operated transactional
datastore, TLS, workload identity, provider registration, secret rotation and callback routes.
