# Module 26 — Runtime credential broker boundary

Module 26 lets an approved API run reference an operator-owned bearer credential without putting
its value in a runner request, signed action, generated test, plan, audit record, or evidence.
The request contains only a validated alias such as `staging-api`.

At execution time, the broker maps that alias to `SPECVORA_CREDENTIAL_STAGING_API`, validates the
value and gives the child process only `SPECVORA_RUNTIME_AUTHORIZATION`. Generated Pytest/HTTPX
code reads this runtime value and disables ambient HTTP proxy configuration with `trust_env=False`.
Captured standard output and error are redacted before they enter the runner outcome.

## Operator workflow

Run `scripts/setup-runtime-credential.ps1 -Alias staging-api -ApproveSetup` and enter the value at
the hidden prompts. The script sets it only in the current PowerShell process and never writes or
prints it. Add `--credential-alias staging-api` to `specvora run-pytest`.

The alias is part of the signed execution action. Changing it invalidates the approval. The secret
value is deliberately excluded so rotation does not serialize or sign secret material.

## Security boundary

- only bearer credentials are supported in this module;
- aliases, not secret values, belong in durable artifacts;
- missing, short, oversized, newline-containing, or NUL-containing values fail before execution;
- arbitrary parent environment variables remain filtered;
- generated code can use the credential while running and must therefore be reviewed and covered
  by the signed artifact hash;
- exact-value redaction limits accidental output exposure but is not a general data-loss-prevention
  system and cannot prevent a malicious approved test from transforming or sending the value;
- use short-lived, least-privilege credentials for non-production targets only.

Future production work should replace the environment provider with a managed secret service,
workload identity and auditable leases while preserving the alias-only request contract.
