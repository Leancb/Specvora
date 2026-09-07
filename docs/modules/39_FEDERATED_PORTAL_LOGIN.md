# Module 39 — Federated portal login routes

Module 39 connects the Module 38 transaction and exchange boundary to the portal's existing
revocable session model.

## HTTP lifecycle

1. `GET /api/session/oidc/start` validates runtime configuration, registers the one-use
   transaction and redirects to the configured authorization endpoint.
2. The provider redirects to `GET /api/session/oidc/callback` with code and state.
3. Specvora consumes state, exchanges the code with PKCE, and validates the ID token.
4. The external username must match an active local user. Only that user's local roles apply.
5. Specvora creates its normal signed, server-registered session and redirects to `/portal`.

Provider errors, missing parameters, invalid identities and exchange failures return the same
generic response. Provider descriptions and tokens are never reflected to the browser.

## Runtime configuration

- `SPECVORA_OIDC_AUTHORIZATION_ENDPOINT`
- `SPECVORA_OIDC_TOKEN_ENDPOINT`
- `SPECVORA_OIDC_CLIENT_ID`
- `SPECVORA_OIDC_REDIRECT_URI`
- `SPECVORA_OIDC_TOKEN_ALLOWED_HOSTS` (comma-separated exact hostnames)
- `SPECVORA_OIDC_CLIENT_SECRET` (optional runtime secret)

Module 37 issuer, audience and JWKS settings are also required. Local HTTP callback URIs are
accepted only for `127.0.0.1` or `localhost`; deployed callbacks must use HTTPS.

Federated login identifies a human but does not replace signed approval, deterministic policy,
runner confinement or release accountability.
