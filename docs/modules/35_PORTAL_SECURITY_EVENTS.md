# Module 35 — Structured portal security events

Module 35 records a minimal, append-only security trail in the selected transactional state
backend. Events cover failed, throttled and successful login, recovery-code use and recovery-set
rotation. Each row contains only an enumerated event type, normalized subject hash and
timezone-aware timestamp.

SQLite persists events in an ordered table. The central service exposes an authenticated
`POST /v1/security-events` contract, and the HTTPS adapter rejects every unexpected status.
Arbitrary event names and free-form metadata are not accepted, preventing passwords, TOTP codes,
recovery codes and bearer values from entering this channel.

Audit recording is part of the authenticated workflow and fails closed when the selected state
backend cannot persist it. This local trail supports investigation and training; production still
requires protected export, retention policy, access control, alerting, clock assurance and SIEM
correlation. It does not replace the release-evidence hash chain.
