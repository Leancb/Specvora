# Module 40 lab — Controlled OIDC key rotation

## Objective

Rehearse a safe public-key lifecycle without allowing discovery to redefine the issuer.

## Exercise

1. Run `python -m pytest tests/test_oidc_trust.py -q`.
2. Bootstrap key A into a new confined trust file.
3. Rotate to A+B and confirm the file is replaced atomically.
4. Attempt to rotate directly from A to B and confirm rejection with the original file intact.
5. Change the discovered issuer or JWKS hostname and confirm fail-closed behavior.
6. Explain why a human-controlled second rotation from A+B to B is safe after rollout.

For a registered provider, substitute its real values and run:

```powershell
.\scripts\update-oidc-trust.ps1 -Command bootstrap `
  -DiscoveryEndpoint "https://PROVIDER/.well-known/openid-configuration" `
  -Issuer "https://PINNED-ISSUER" -AllowedHost PROVIDER `
  -Output ".specvora-auth\oidc-jwks.json" -ApproveTrustUpdate
```

Never copy client secrets into the command, trust file or training evidence.
