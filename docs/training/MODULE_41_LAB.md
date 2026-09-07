# Module 41 lab — Independent OIDC trust approval

## Objective

Demonstrate separation of duties and trace one public-key change end to end.

## Exercise

1. Run `python -m pytest tests/test_oidc_trust_approval.py -q`.
2. Create an immutable proposal and approval claims:

```powershell
.\scripts\prepare-oidc-trust-change.ps1 -ProjectId portal `
  -DiscoveryEndpoint "https://PROVIDER/.well-known/openid-configuration" `
  -Issuer "https://PINNED-ISSUER" -AllowedHost PROVIDER `
  -Reviewer "SECURITY REVIEWER" -Bootstrap -ApproveDiscovery
```

3. Have the named reviewer inspect the proposal and sign its exact bytes offline with
   `specvora-governance sign`, purpose `oidc-trust-change` and `APPROVED_SIGNING`.
4. A different operator applies the envelope with `apply-oidc-trust-change.ps1` and
   `-ApproveApplication`.
5. Repeat the application and confirm single-use rejection.
6. Modify one audit record and confirm `verify-audit` reports `false`.

Never place the private signing key in the discovery or application environment.
