# Module 17 — Signed approvals and combined release policy

## Delivered contract

The operator-only `specvora-governance` CLI signs detached approval claims with Ed25519,
verifies them against an independently supplied trusted public key, and optionally consumes
the approval once in a persistent SQLite ledger. No private key enters the portal, and no
real signing key is automatically created or enrolled.

Claims bind version, UUID, project, purpose (`proposal-promotion` or `release-review`), reviewer,
exact artifact SHA-256, issuance, and expiry. Signing requires `APPROVED_SIGNING`. Verification
rejects tampering, wrong keys, different artifacts or contexts, naive clocks, future issuance,
and expiry. A signature proves possession of the trusted key, not the reviewer's civil identity.

`verify` is read-only and repeatable. `consume` verifies first, then inserts the approval UUID
under a unique database constraint: concurrent consumers cannot both succeed. All consumers
must use the same durable ledger; deleting or replacing it defeats replay protection. Consumption
does not launch a test or release and is not an atomic transaction with external deployment.

## Combined decision

`CombinedReleaseRequest` requires API and browser normalized `TestRunResult` values, one project,
distinct run IDs, an operator-selected release ID, and the existing confidence policy. Each suite
is evaluated independently. The worst decision wins: BLOCK > HUMAN_REVIEW > RELEASE. Scores and
coverage totals are never averaged or added, so shared requirements are not double-counted.
The result retains both assessments and is explicitly a recommendation, not deployment authority.

This interface consumes normalized results; it does not authenticate raw reports or independently
prove that both runs tested the same build. Operators must supply evidence for the selected release.

## Compatibility and limitations

This module adds an operator workflow without silently changing existing CLI/portal approval
semantics. Existing unsigned portal decisions remain unsigned. Mandatory signature enforcement
in the portal and executors, identity binding, key rotation/revocation, encrypted key storage,
and authenticated multi-user deployment remain separate work. Do not expose the portal publicly.
Key files are raw 32-byte Ed25519 keys, selected explicitly by the operator and stored outside Git.
Use temporary keys only for the included lab. The implementation follows the library's documented
[Ed25519 API](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/).

## Verification

Tests exercise real signatures, changed artifacts/claims, wrong keys/context/time, persistent and
concurrent consumption, CLI round trips, immutable output files, and mixed-project/run rejection.
