# Module 25 — Controlled authentication and dependency adapters

Module 25 extends promoted test generation with deterministic adapters for authentication
and dependency failures. The OpenAPI operation must document the expected response and the
adapter explicitly; Specvora never invents credentials or production behavior.

## Authentication contract

Use `x-specvora-auth-fixtures` with the dedicated `X-Specvora-Auth-Fixture` request header.
Accepted values are `valid`, `missing`, `expired`, and `insufficient-scope`. An authenticated
operation without this adapter is blocked. Values that resemble bearer tokens, API keys, or
other credentials are rejected.

The adapter verifies generated-test behavior against a controlled target. It does not test a
real identity provider, token signature, MFA flow, or authorization server integration.

## Dependency contract

Use `x-specvora-dependency-fixtures` with `X-Specvora-Dependency-Fixture`. Accepted values are
`unavailable` and `timeout`. Both produce a deterministic documented 503 response in the local
fixture application. The timeout case does not sleep, so training and CI remain repeatable.

The original `x-specvora-test-fixtures` resilience adapter remains compatible. Specvora blocks
an operation when multiple adapters could claim the same expected response.

## Safety boundary

- control headers are allowed only on isolated local or non-production fixture targets;
- production services must never honor these headers;
- a fixture-backed negative starts from a schema-valid deterministic request case;
- generation remains separate from signed execution authorization;
- host allowlisting, workspace confinement, fixed commands, evidence, and one-use approval
  controls still apply.

This module broadens deterministic test coverage without granting the model, the portal, or a
fixture authority to approve execution or release.
