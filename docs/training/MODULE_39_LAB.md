# Module 39 lab — Federated portal session

## Objective

Trace a federated identity from browser redirect to a locally authorized, revocable session.

## Exercise

1. Run `python -m pytest tests/test_portal_auth_integration.py -q`.
2. Inspect `/api/session/oidc/start` and verify its destination is fixed by runtime configuration.
3. Follow the callback test through transaction consumption, identity mapping and session issue.
4. Add a remote `operator` claim and verify that the local user keeps only local roles.
5. Submit an IdP error description and confirm that it is not reflected in the response.
6. Remove one configuration value and confirm the start route fails closed.

## Discussion

The identity provider proves identity. Specvora owns application roles, policy decisions,
one-use human approvals and the confined execution boundary.
