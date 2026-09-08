# Module 43 — Authenticated, idempotent OIDC alert delivery

Module 43 delivers Module 42 findings without granting the receiver or monitor authority over
identity trust.

## Delivery contract

- `HEALTHY` reports produce no network request.
- `REVIEW_REQUIRED` becomes `WARNING`; `BLOCKED` becomes `CRITICAL`.
- The payload has a fixed schema containing only issuer, hashes, public key IDs, findings and time.
- A SHA-256 alert ID excludes observation time, so repeated observations of the same condition
  carry the same `Idempotency-Key`.
- The receiver must be an exact allowlisted HTTPS destination without embedded credentials,
  query strings or fragments.
- Authentication uses `SPECVORA_OIDC_ALERT_TOKEN` from the process environment only.
- Redirects and ambient proxies are disabled. HTTP 429, server failures and network errors receive
  at most three bounded attempts.
- Receiver bodies, credentials and remote details are excluded from errors.

`scripts/monitor-and-alert-oidc.ps1` writes an immutable report and passes it to the delivery CLI.
The script contains no call to trust proposal or application code.

HTTP idempotency requires receiver-side enforcement. Production must add managed workload
identity, receiver retention, paging ownership, scheduling and measurable alert SLOs.
