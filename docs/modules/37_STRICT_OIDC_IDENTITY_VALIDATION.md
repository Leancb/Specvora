# Module 37 — Strict OIDC identity validation

Module 37 establishes the cryptographic trust boundary for external identity federation. It
validates compact OIDC ID tokens against a locally provisioned JWKS file and exact HTTPS issuer,
audience and expected nonce configuration.

Only `RS256` with a unique known `kid`, RSA keys of at least 2048 bits and exponent 65537 are
accepted. Signature, `iss`, `aud`, multi-audience `azp`, `exp`, `iat`, optional `nbf`, nonce,
subject and normalized username are checked with a bounded 60-second clock tolerance. Unsafe or
malformed configuration produces one generic validation failure.

The external username must map to an active user already configured in Specvora. Roles and groups
inside the token are ignored: portal authorization remains locally controlled. Federated
authentication also requires transactional state so security events cannot silently disappear.

This module intentionally does not expose a browser token-submission endpoint. A production login
must add Authorization Code + PKCE, one-use server-side state/nonce, secure callback handling and
provider metadata/key rotation. Accepting an arbitrary token and caller-supplied nonce would not
be a safe federation flow.
