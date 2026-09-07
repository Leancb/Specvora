# Module 38 lab — OIDC PKCE transaction lifecycle

## Objective

Explain and verify why a browser callback can be accepted exactly once.

## Exercise

1. Run `python -m pytest tests/test_oidc_flow.py tests/test_portal_session_store.py -q`.
2. Identify `state`, nonce and the `S256` challenge in the authorization URL.
3. Confirm that the SQLite row contains a digest instead of raw `state`.
4. Observe that the transaction is deleted before token exchange.
5. Repeat the callback and confirm rejection before a second provider request.
6. Change the token hostname and confirm deterministic allowlist rejection.

State provides correlation, nonce binds the ID token, and PKCE binds the code to the server
transaction. Signed human approval remains the separate execution and release boundary.
