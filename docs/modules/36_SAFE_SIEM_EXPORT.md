# Module 36 — Safe SIEM security-event export

Module 36 exports Module 35 events incrementally to an explicitly allowed HTTPS collector. The
export reads the portal SQLite database in read-only mode and sends only the fixed event schema:
event ID, enumerated type, subject hash and timezone-aware timestamp.

Each canonical batch receives a SHA-256 idempotency key. A confined checkpoint advances only
after `200` or `202`; failure, timeout, `429` and server errors retain the previous checkpoint.
Transient failures receive at most three attempts with bounded exponential delays. Redirects and
ambient proxy configuration are disabled.

The destination hostname must match an explicit allowlist. Credentials in URLs, plaintext HTTP,
short/whitespace-bearing tokens and escaped database/checkpoint paths are rejected. The bearer is
read from `SPECVORA_SIEM_TOKEN` at runtime and is never included in batch content or output.

Use `scripts/export-portal-security.ps1` with `-ApproveExport`. This is a controlled exporter, not
a complete SIEM integration: production needs workload identity, receiver-side idempotency,
certificate policy, monitoring, retention, dead-letter handling and operational ownership.
