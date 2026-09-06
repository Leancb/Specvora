# Module 24 — Authenticated portal sessions and roles

Module 24 adds local identities, signed sessions and role authorization to the review portal.
Authentication does not replace the detached Ed25519 approval: a logged-in reviewer identifies
the person using the portal, while the offline signature authorizes the immutable action.

## Session boundary

Passwords are stored only as salted PBKDF2-HMAC-SHA256 hashes with 600,000 iterations. A random
32-byte key signs short-lived session cookies. Cookies are `HttpOnly`, `SameSite=Strict` and
secure by default. State-changing requests also require the session's CSRF token.

Every request reloads the user record. Setting `active` to false or incrementing
`session_version` revokes existing sessions without changing the session key. Replacing the key
revokes every session.

## Roles

- `viewer`: list projects, reviews and generation details; ingest evidence.
- `reviewer`: viewer capabilities plus approval-payload preparation and human decisions.
- `operator`: viewer capabilities plus project/review registration, plan generation, analysis
  and assessment.

A user may hold multiple roles. In authenticated mode, the decision's reviewer name must exactly
match the current user's display name. No role can bypass signed approval policy.

## Modes and limitations

`SPECVORA_PORTAL_AUTH_MODE=required` enables enforcement. The default
`local-development` mode preserves existing loopback labs and is forbidden for network exposure.
The current identity store is a confined local JSON file intended for the MVP, not multi-node
production. Rate limiting, MFA, password reset and external identity federation remain future
hardening. Use HTTPS with `SPECVORA_PORTAL_COOKIE_SECURE=true` outside loopback training.
