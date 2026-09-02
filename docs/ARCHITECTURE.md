# Architecture

Specvora separates proposals from authority. The deterministic pipeline validates a project input and OpenAPI 3 contract, extracts operations, derives scenarios, and writes customer-owned artifacts. Generated code is data until a human explicitly approves execution.

`ProjectInput -> OpenAPI parser -> deterministic analyzer -> artifact generator`

The execution policy is a separate trust boundary. API and browser runs require distinct
exact approval tokens, match target hosts against explicit allowlists, confine inputs and
reports to the selected workspace, and construct fixed commands without a shell. Generated
Playwright journeys also block page requests outside the reviewed host list.

AI assistance remains optional and is deliberately outside the deterministic core.
Application-level browser controls do not replace future container and OS egress isolation.
