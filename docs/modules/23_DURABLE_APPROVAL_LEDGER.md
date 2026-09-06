# Module 23 — Durable atomic approval ledger

Module 23 closes the hosted-runner replay gap from Module 22. After validating the detached
Ed25519 signature, the controller atomically creates the Git reference
`refs/tags/specvora-approvals/<approval-id>`. GitHub rejects creation when that reference
already exists, so a second workflow cannot consume the same approval.

## Order of enforcement

1. Validate the reviewed action, signature, project, purpose, reviewer and expiry.
2. Claim the approval UUID in the configured ledger.
3. Start the fixed, confined test subprocess only after the claim succeeds.

An invalid signature never writes to the ledger. A successfully claimed approval is burned even
if the later test execution fails; safety takes precedence over retry convenience. A retry needs
a newly reviewed and signed envelope.

## GitHub backend

Set `SPECVORA_APPROVAL_LEDGER_BACKEND=github-ref` together with repository, commit SHA and a
short-lived token. The workflow uses its scoped `github.token` only in the controller process.
The filtered Pytest environment does not receive it. The tag points to the exact workflow commit,
while its name records the approval UUID without storing the signed envelope or private key.

Creating a Git reference requires `contents: write`. Checkout credentials remain unpersisted,
the workflow remains manual and protected by the `specvora-governed` environment, and generated
tests still execute with a filtered environment. The local default remains the SQLite backend.

## Operational boundary

The guarantee depends on retaining the `specvora-approvals/*` references. Protect this tag
namespace with repository rules and restrict deletion. A repository administrator can still
delete a reference, so exported audit/evidence and administrative controls remain necessary.
This backend is suitable for the current single-repository CI design; a future multi-tenant
service should use a dedicated transactional ledger with independent access control.
