# Module 29 — Portal state backend contract

Module 29 separates portal authentication from its persistence implementation through the
`PortalSessionState` protocol. Authentication depends only on atomic MFA claim, session register,
active-session lookup and revocation operations.

`SPECVORA_PORTAL_STATE_BACKEND=sqlite` selects the implemented local backend and requires
`SPECVORA_PORTAL_STATE_DB`. Existing environments that define only the database path remain
compatible. Unknown backends and incomplete configuration fail closed.

This is an architectural seam, not a distributed datastore implementation. A future centralized
adapter must prove atomic claims, consistent revocation, expiry semantics, TLS authentication,
availability behavior and tenant isolation with integration and concurrency tests before use.
