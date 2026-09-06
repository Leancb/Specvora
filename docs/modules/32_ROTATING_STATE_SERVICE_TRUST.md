# Module 32 — Rotating state-service trust

Module 32 adds bounded credential rotation to the central portal-state service. When
`SPECVORA_STATE_SERVICE_TOKEN_FILE` is configured, the service reads a strict JSON trust file
containing one to eight SHA-256 token digests and their `not_before`/`expires_at` windows. The
plaintext bearer remains only in the calling process or secret provider.

The trust-file mode takes precedence over `SPECVORA_STATE_SERVICE_TOKEN`. Active overlapping
entries allow a controlled handover between callers; expired and not-yet-valid entries are
rejected. Unknown fields, malformed hashes, naive timestamps, inverted windows, oversized files
and unreadable configuration all fail with the same generic authentication response.

Example structure (illustrative digests only):

```json
{
  "version": "specvora-state-service-trust-v1",
  "tokens": [
    {
      "token_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "not_before": "2026-09-06T12:00:00Z",
      "expires_at": "2026-09-06T12:30:00Z"
    }
  ]
}
```

This is a rotation and non-disclosure improvement, not workload identity. Production still needs
a managed identity/secret provider, atomic distribution, revocation procedures and audit events.
