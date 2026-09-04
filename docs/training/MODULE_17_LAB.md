# Module 17 lab — Signatures and combined decisions

## Setup

From `D:\Specvora`, update dependencies with `python -m pip install -e ".[dev]"`.
Run `python -m pytest tests/test_signed_governance.py -q` to exercise disposable signing keys,
API/browser policy outcomes, immutable artifacts, and concurrent replay rejection. These tests
do not create an operational signing identity or require OpenAI credits.

## Operator command reference

All artifact paths must be inside `--workspace-root`. Outputs refuse overwrite. Key paths are
explicit operator inputs and may be outside the workspace. Never paste private key bytes into
Swagger, chat, source code, or logs.

```powershell
specvora-governance --workspace-root . assess-combined combined-input.json --output result.json
specvora-governance --workspace-root . sign claims.json --artifact review.json --private-key C:\secure\signing.key --approval APPROVED_SIGNING --output signed.json
specvora-governance --workspace-root . verify signed.json --artifact review.json --public-key C:\secure\trusted-public.key --project-id petstore-demo --purpose proposal-promotion
specvora-governance --workspace-root . consume signed.json --artifact review.json --public-key C:\secure\trusted-public.key --project-id petstore-demo --purpose proposal-promotion --ledger workspaces\consumed.db
```

These are templates, not ready-to-run production approvals. `claims.json` follows ApprovalClaims:
project_id, purpose, reviewer, artifact_sha256, issued_at and expires_at (timezone-aware ISO dates).
The UUID and version have defaults. `combined-input.json` contains project_id, release_id, api and
browser (each a normalized TestRunResult), plus optional policy. Use the test fixtures as examples.

## Demonstration

1. Explain why SHA-256 alone does not establish who approved a record.
2. Run the CLI roundtrip test and show that changing a signed claim breaks verification.
3. Compare repeatable verification with one-time consumption using the same ledger.
4. Make the browser suite fail critically while API passes: combined decision must be BLOCK.
5. Explain why neither a signed record nor RELEASE automatically deploys anything.

## Trainer warning

The portal still uses the prior unsigned workflow. This module does not make it safe for public
hosting. Trusted-key enrollment and mandatory signed authorization need a separate integration.
