# Module 42 lab — OIDC trust monitoring

## Objective

Classify provider and local trust changes without modifying trusted keys.

## Exercise

1. Run `python -m pytest tests/test_oidc_monitor.py -q`.
2. Monitor matching local and discovered key A; expect `HEALTHY`.
3. Publish A+B in the controlled fixture; expect `REVIEW_REQUIRED`.
4. Publish only B; expect `BLOCKED` because no trusted overlap remains.
5. Modify a valid local JWKS outside governance; expect `TRUST_AUDIT_MISMATCH`.
6. Modify or remove the audit log; expect `AUDIT_INVALID`.
7. Compare trust and audit bytes before and after every check to prove read-only behavior.

For a configured provider, use `scripts/check-oidc-trust.ps1` with the exact issuer, discovery URL
and allowed hostnames. A review alert begins Module 41; it never applies the discovered keys.
