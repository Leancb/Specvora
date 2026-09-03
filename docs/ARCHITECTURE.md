# Architecture

Specvora separates proposals from authority. The deterministic pipeline validates a project input and OpenAPI 3 contract, extracts operations, derives scenarios, and writes customer-owned artifacts. Generated code is data until a human explicitly approves execution.

`ProjectInput -> OpenAPI parser -> deterministic analyzer -> artifact generator`

The execution policy is a separate trust boundary. API and browser runs require distinct
exact approval tokens, match target hosts against explicit allowlists, confine inputs and
reports to the selected workspace, and construct fixed commands without a shell. Generated
Playwright journeys also block page requests outside the reviewed host list.

AI assistance remains optional and is deliberately outside the deterministic core.
Application-level browser controls do not replace future container and OS egress isolation.

Both Pytest and Playwright reports enter source-specific fail-closed normalizers. Each
normalizer produces hashed evidence and the shared `TestRunResult` contract, allowing one
deterministic confidence engine and audit chain without pretending the raw formats match.

The optional AI proposer sits outside this deterministic path. A single tool-free agent
returns typed scenario metadata. Specvora records model and prompt provenance, applies
local semantic policy, and stores a proposal-only envelope. It does not merge proposals
into analysis, generation, execution, or confidence automatically.
