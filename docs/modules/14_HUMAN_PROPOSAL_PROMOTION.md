# Module 14 — Human Review and AI Proposal Promotion

## Objective

Turn a policy-valid AI proposal into an accountable human decision and a separate,
maintained scenario catalog without granting automatic generation or execution authority.

## Review contract

The reviewer supplies a JSON decision document containing:

- an identified reviewer;
- the exact token `APPROVED_PROPOSAL_PROMOTION`;
- one `ACCEPT` or `REJECT` decision for every proposal;
- a human rationale for every decision.

The decision set must cover exactly the proposal IDs. Missing, unknown, or duplicate
decisions fail closed. A proposal envelope marked `BLOCKED`, or containing deterministic
findings, cannot be promoted.

The original project file is required again. Specvora reconstructs the minimized proposal
input, verifies its hash, and repeats semantic validation against the current OpenAPI
contract before processing the human decision.

## Integrity and immutability

Specvora calculates SHA-256 for both the original AI envelope and the human decision file.
Those hashes are stored in the review record and promotion catalog, binding the outcome to
the exact inputs that were reviewed.

Review and catalog output paths must be distinct JSON files inside the workspace. Existing
outputs are immutable and never overwritten; a new review requires new paths.

## Outputs

`review-record.json` records the reviewer, timestamp, input hashes, all decisions, accepted
and rejected counts, and the catalog location.

`promoted-scenarios.json` contains only accepted proposals, assigns `PROM-AI-*` scenario
IDs, preserves source proposal IDs, and records `human-approved` authority.

If every proposal is rejected, the review is still recorded as
`REVIEWED_NO_PROMOTION` and the catalog remains empty.

## Authority boundary

Promotion means that a person accepted scenario intent into a maintained catalog. It does
not create Pytest or Playwright code, modify the deterministic analysis, authorize a test
run, or make a release decision. Those remain separate controlled transitions.
