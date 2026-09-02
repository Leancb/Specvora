# Architecture

Specvora separates proposals from authority. The deterministic pipeline validates a project input and OpenAPI 3 contract, extracts operations, derives scenarios, and writes customer-owned artifacts. Generated code is data until a human explicitly approves execution.

`ProjectInput -> OpenAPI parser -> deterministic analyzer -> artifact generator`

The execution policy is a separate trust boundary. It requires the exact approval token, matches the URL host against an explicit allowlist, confines the test path to the selected workspace, and returns only a fixed Pytest command. The MVP does not execute arbitrary AI-proposed commands.

AI assistance remains optional and is deliberately outside the deterministic core. Future Playwright generation must pass through the same validation and approval boundary.
