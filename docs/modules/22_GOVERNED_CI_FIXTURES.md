# Module 22 — Governed fixture execution in CI

Module 22 adds a manually dispatched GitHub Actions workflow for the controlled 429/503
fixture plan. The private Ed25519 key remains on the operator machine. CI receives only the
raw public key and a short-lived signed envelope through protected environment secrets.

## Portable signed action

Set `SPECVORA_ACTION_PATH_MODE=workspace-relative` while preparing and consuming the action.
The `execution-v2-portable` document replaces the physical workspace root with `$WORKSPACE`
and records generated/report paths relative to it. File hashes, target URL, allowlist,
approval token and timeout remain signed. The default is still `execution-v1` with absolute
paths, preserving existing local behavior.

Portable mode does not weaken confinement: generation and report paths must first resolve
inside the real workspace. Invalid modes, escaped reports, changed artifacts and changed
request controls are rejected.

## Workflow boundary

`.github/workflows/governed-fixtures.yml` is `workflow_dispatch` only, has read-only contents
permission, disables persisted checkout credentials and targets the protected
`specvora-governed` environment. It materializes secrets without printing them, validates
the detached signature, starts the fixture API on loopback, executes only through
`specvora run-pytest`, and uploads evidence with a unique immutable artifact name.

The committed `ci/module22-plan` is the reviewed executable artifact. Any commit that changes
it invalidates an envelope prepared from the earlier tree.

## Replay protection evolution

Module 22 originally used a runner-local SQLite ledger, which was not durable across hosted
runs. Module 23 replaces that CI limitation with an atomic Git-reference claim while preserving
SQLite for local execution. The protected environment must still require a reviewer; the
envelope should expire quickly and `SPECVORA_CI_SIGNED_APPROVAL_B64` must be deleted immediately
after the run. See `23_DURABLE_APPROVAL_LEDGER.md`.

The workflow recommendation is evidence, never deployment authority. It has no deployment
job and no production credentials.
