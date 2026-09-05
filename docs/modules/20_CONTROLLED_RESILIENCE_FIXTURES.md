# Module 20 — Controlled resilience fixtures

Module 20 permits promoted 429/503 scenarios only when the OpenAPI operation both documents
the response and declares an explicit `x-specvora-test-fixtures` adapter. Generation remains
offline; execution still requires the signed runner, allowlisted host and confined artifacts.

```yaml
responses:
  '429': {description: Controlled rate limit}
x-specvora-test-fixtures:
  '429':
    kind: request-header
    name: X-Specvora-Fixture
    value: rate-limit
```

The MVP accepts exactly one adapter: `request-header` with the dedicated
`X-Specvora-Fixture` name and a lowercase, bounded token value. Arbitrary headers,
credentials, multiple expected statuses and unsafe values are rejected. A fixture-backed
negative scenario must bind to a schema-valid baseline case so the injected condition is
the only intended cause of failure.

`specvora.fixture_app:app` is a local training target. It returns 200 normally, 429 for
`rate-limit`, 503 for `dependency-failure`, and 400 for unknown fixture values. It must not
be deployed as a production service or exposed publicly.

The extension is a test contract, not proof that a production dependency behaves this way.
Use a dedicated non-production target. Human promotion does not authorize execution, and
READY_FOR_HUMAN_APPROVAL still requires a new artifact-bound signature.
