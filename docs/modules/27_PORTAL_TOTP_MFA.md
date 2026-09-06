# Module 27 — Portal TOTP multi-factor authentication

Module 27 adds optional per-user TOTP enrollment to the authenticated local portal. Once enrolled,
password-only login fails and the portal requires a six-digit time-based code. Existing users remain
compatible until an operator explicitly enrolls them.

TOTP uses a 30-second SHA-1 construction compatible with RFC 6238 and accepts the immediately
previous, current, or next interval to tolerate limited clock skew. A successful counter is stored
on the user record; that counter and every older counter are rejected on reuse. Enrollment increments
`session_version`, revoking the user's existing portal sessions.

## Enrollment boundary

`scripts/enable-portal-mfa.ps1` requires `-ApproveEnrollment`. It writes an `otpauth_uri` to a new,
confined file under `.specvora-auth/` without printing the secret. The operator imports that URI into
an authenticator, verifies login, then removes the enrollment file. The user database still contains
the TOTP seed and must be protected as sensitive authentication material.

## Remaining limitations

- this is local TOTP, not external identity federation or phishing-resistant authentication;
- there are no recovery codes, device lifecycle, administrative reset, or login rate limits yet;
- replay persistence uses atomic file replacement but has no cross-process transaction or lock;
- clock synchronization is an operator responsibility;
- filesystem permissions and backups must protect `.specvora-auth/users.json`;
- multi-node deployment requires centralized transactional session and MFA state.

MFA strengthens portal login only. It does not replace role checks, CSRF, the purpose-bound offline
Ed25519 execution approval, allowlisting, confinement, evidence, or accountable release authority.
