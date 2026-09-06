# Module 30 — Centralized HTTP state adapter

Module 30 implements the Module 29 contract as an HTTPS client for a centralized state service.
Select `SPECVORA_PORTAL_STATE_BACKEND=http`, provide `SPECVORA_PORTAL_STATE_ENDPOINT` and inject
`SPECVORA_PORTAL_STATE_TOKEN` at runtime. Credentials in URLs, plaintext HTTP, short tokens,
redirects and ambient proxy settings are rejected or disabled.

The adapter supports atomic MFA claims, session registration, active lookup and revocation with
strict status and response validation. Transport failures expose only a generic error and never
the service token or remote response body.

This delivers the production-facing client boundary, not the hosted service itself. Deployment
still requires an independently secured service implementing `/v1/mfa-claims` and `/v1/sessions`,
with atomic storage, TLS, token rotation, availability monitoring and tenant isolation.
