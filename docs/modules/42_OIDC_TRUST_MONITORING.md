# Module 42 — Deterministic OIDC trust monitoring

Module 42 observes identity trust without acquiring authority to change it.

## Status model

- `HEALTHY`: current JWKS is valid, its canonical hash matches the last governed audit record,
  discovery is valid and the provider publishes the same key set.
- `REVIEW_REQUIRED`: the provider key set changed but still overlaps current trust. A Module 41
  proposal and independent approval are required.
- `BLOCKED`: trust/audit is invalid, an out-of-band local change occurred, discovery failed, or
  provider keys have no trusted overlap.

Reports contain issuer, canonical hashes, public key IDs, time and enumerated findings. Remote
response bodies and secrets are excluded. The monitor uses the same issuer pinning, HTTPS
allowlists, response limits, disabled redirects and disabled ambient proxies as discovery.

`scripts/check-oidc-trust.ps1` is read-only. It turns review and blocking states into visible
PowerShell failures for schedulers, but never invokes proposal, approval or application commands.

Production still needs scheduling, delivery to an authenticated alert receiver, ownership,
severity policy and service-level objectives. Monitoring never authorizes automatic rotation.
