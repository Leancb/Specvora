# Module 40 — Pinned OIDC discovery and JWKS rotation

Module 40 turns JWKS provisioning into an explicit operator workflow while retaining a pinned
trust boundary.

## Deterministic controls

- The configured issuer must exactly match discovery metadata.
- Discovery, authorization, token and JWKS endpoints must use HTTPS and exact allowlisted hosts.
- Discovery must advertise Authorization Code, `RS256` and PKCE `S256`.
- Every downloaded key must be a unique, valid RSA signing key of at least 2048 bits with
  exponent 65537.
- Bootstrap requires an absent trust file; rotation requires an existing valid trust file.
- Rotation requires at least one trusted `kid` to overlap, enabling staged `A → A+B → B` change.
- Canonical JWKS bytes replace the trust file atomically only after every validation succeeds.
- Redirects and ambient proxy settings are disabled.

An operator must use `-ApproveTrustUpdate` with `scripts/update-oidc-trust.ps1`. This workflow
updates public verification material only; it never downloads or stores client secrets.

Provider compromise, DNS/network controls, certificate governance and approval ownership remain
deployment responsibilities. Automatic unreviewed key acceptance is intentionally excluded.
