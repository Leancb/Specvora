# Module 18 — Signed authorization in the portal and runners

## Change contract

Portal decisions and both controlled runners now require a valid signed action by default.
Existing explicit approval tokens, host allowlists, reviewed browser plan and quality gates
still apply. Only operator-owned process configuration can select `local-development` mode;
no request field supplies a trusted key, ledger path, or an authorization bypass.

Required server configuration:

- `SPECVORA_AUTH_MODE=signed` (the default when absent; unknown values are rejected);
- `SPECVORA_TRUSTED_PUBLIC_KEY`: path to a raw 32-byte Ed25519 public key;
- `SPECVORA_APPROVER_NAME`: exact reviewer name enrolled by the operator for that key;
- `SPECVORA_APPROVAL_LEDGER`: shared durable SQLite consumption ledger path.

No operational keys are generated or enrolled automatically. Matching a configured key/name
is not a login system or a legally verified identity. Portal access remains local-only.

## Action binding

The portal signs canonical JSON containing review ID, project ID, source project/OpenAPI/proposal
hashes, and the entire human decision. The proposal must still match the hash captured when queued.
`POST /api/reviews/{id}/approval-payload` returns exact UTF-8 artifact text and its SHA-256 without
promoting or consuming anything. The final decision includes a `signed_approval` envelope and the
server reconstructs the action instead of trusting a client-supplied action hash.

Executors use distinct `api-execution` and `browser-execution` purposes. Canonical execution
actions bind request fields, project ID, target, allowed hosts, timeout, absolute workspace/report
paths and hashes of generated files. The signature itself is excluded. Dependencies in node_modules,
Python bytecode caches and pytest caches are excluded and remain trusted runtime dependencies.
`specvora-governance prepare-execution` exports these exact bytes from a runner request JSON.
Keep exported actions, signatures and reports outside the generated input directory.

## Consumption and failure behavior

Approval is verified and consumed before decision files or subprocess launch. The approval ID is
returned in runner outcomes and portal results; the portal also stores the signed envelope inside
the immutable decision file. If execution, filesystem output, or database completion subsequently
fails, consumption is not rolled back. An operator must investigate and issue a new approval.
Consumption is at-most-once authorization, not an atomic deployment transaction.

The workspace and runtime remain operator-controlled. This module does not prevent a hostile
local process from racing file mutations between hashing and use, nor sandbox Python imports.
Use separate OS/container boundaries for hostile code. The earlier direct `review-ai` offline
CLI remains a local authoring workflow; it is not a substitute for portal authorization.

## Migration

Unsigned portal POSTs and runners now fail closed unless the operator deliberately starts the
process with `SPECVORA_AUTH_MODE=local-development`. That compatibility mode is for trusted
local labs only. Legacy tests explicitly select it; new integration tests exercise default signed
mode with disposable keys. No existing records are rewritten and no existing approval is signed
retroactively. Restart the server after updating configuration; reloading code alone is insufficient.
