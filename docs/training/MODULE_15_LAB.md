# Training lab — Module 15

## Objective

Demonstrate that an approved hostname is converted into a hash-linked default-deny OS
policy and understand the operational conditions required for real container enforcement.

## Exercise

```powershell
specvora create-egress-policy `
  --target-url http://localhost:8080 `
  --allowed-host localhost `
  --approval APPROVED_EGRESS_POLICY `
  --workspace-root . `
  --policy-dir workspaces\petstore-demo\egress\run-001

specvora verify-egress-policy `
  workspaces\petstore-demo\egress\run-001\egress-policy.json `
  workspaces\petstore-demo\egress\run-001\specvora-egress.nft `
  --workspace-root .
```

1. Inspect the recorded addresses, port, authority, and rules hash.
2. Confirm that the output chain says `policy drop` and contains no general accept rule.
3. Modify one byte in the rules and confirm verification fails.
4. Try the ordinary `APPROVED` token and confirm policy creation fails.
5. Review `deploy/egress/entrypoint.sh` and identify when privileges are removed.
6. Discuss why address rotation creates a new review event rather than an automatic update.

## Completion evidence

The learner can explain the three separate decisions: application destination policy, human
execution approval, and OS-enforced network reachability.
