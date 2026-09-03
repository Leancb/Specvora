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

Human promotion is another explicit boundary. A complete decision document is validated
against the policy-ready envelope; both inputs are hashed into an immutable review record,
and accepted scenario intent enters a separate catalog. The catalog is not executable and
does not mutate deterministic artifacts.

The isolated execution profile adds a lower network boundary. Specvora resolves the approved
hostname once, pins the resulting IPv4/IPv6 addresses and TCP port, and emits a hashed
default-deny `nftables` ruleset. A Linux container applies that ruleset while it still has
`CAP_NET_ADMIN`, then drops identity, privileges, and the complete capability bounding set
before starting the fixed test command. DNS is not opened inside the runtime; the reviewed
hostname must be pinned in the container hosts file to the same recorded address.

The local portal adds a durable coordination layer without moving policy authority into the
UI. SQLite stores registered projects, proposal hashes, and review state. Files remain the
source artifacts and must be confined to each registered workspace. A portal decision calls
the same deterministic promotion service as the CLI, then persists links to its immutable
review record and promotion catalog.
