# Module 18 lab — Enforced signatures

## Safe first exercise

Use PowerShell in `D:\Specvora`:

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/test_authorization_integration.py -q
```

The tests create only temporary keys. They cover both runners and the real portal API/database
workflow, missing signatures, replay, request/file drift, and server identity/configuration checks.
They do not start an external test target or enroll a production identity.

## Operator configuration

With an independently enrolled signing key, configure the process environment before launching:

```powershell
$env:SPECVORA_AUTH_MODE = "signed"
$env:SPECVORA_TRUSTED_PUBLIC_KEY = "C:\secure\trusted-public.key"
$env:SPECVORA_APPROVER_NAME = "Leandro do Couto Brum"
$env:SPECVORA_APPROVAL_LEDGER = "D:\Specvora\workspaces\consumed.db"
python -m uvicorn specvora.main:app --host 127.0.0.1 --port 8100
```

These key paths are placeholders: provision keys securely first. Do not place a private key in
Swagger, the portal or the repository. Plain `.env` values are not automatically loaded by this
authorization module. Use the process environment explicitly.

## Portal workflow

1. Prepare the complete human decision (same fields as Module 16).
2. POST it to `/api/reviews/{id}/approval-payload`; save the returned `artifact` string as UTF-8,
   without an added newline or BOM. The browser review flow downloads `review-action.json`.
3. Create Module 17 approval claims using the returned hash, enrolled reviewer, project ID,
   `proposal-promotion` purpose and timezone-aware validity period.
4. Sign that exact action offline with `specvora-governance sign` (Module 17 lab).
5. Submit the original decision plus `signed_approval`, or paste the signed envelope into the
   portal prompt. Do not call `consume` manually: the portal consumes it during authorization.
6. Change a rationale or reuse the approval and demonstrate rejection.

## Runner workflow

Build a RunnerRequest or PlaywrightRunnerRequest JSON with explicit project_id, workspace_root,
generated_dir, report_path, base_url (API) or web_base_url, allowed_hosts, approval, timeout_seconds.

```powershell
specvora-governance --workspace-root D:\Specvora prepare-execution request.json --kind api --output action.json
```

Sign `action.json` with purpose `api-execution` (or `browser-execution` for `--kind browser`). Pass
the resulting envelope file with `--signed-approval signed.json` to the corresponding `specvora
run-pytest` or `run-playwright` command, using the exact same request values. Browser execution now
also accepts `--project-id`. API evidence/audit arguments remain required as in the earlier lab.

## Compatibility lab only

To run old unsigned exercises on a trusted local machine, explicitly set
`$env:SPECVORA_AUTH_MODE = "local-development"` before starting the server/runner. This disables
signature enforcement for that process, not the older deterministic controls. Never describe
this mode as signed authorization or deploy it publicly.
