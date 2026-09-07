# Module 34 — One-use MFA recovery

Module 34 adds operator-generated recovery codes for local TOTP identities. A set contains eight
independent high-entropy codes. Plaintext appears once in a confined output selected by the
operator; only domain-separated SHA-256 digests enter transactional portal state.

Recovery requires the correct password and an enabled transactional backend. A successful claim
deletes exactly one digest atomically, clears the login-attempt window and advances the user's
session version so older portal sessions become invalid. Generating a replacement set atomically
removes every digest from the previous set.

Use `scripts/generate-portal-recovery.ps1 -ApproveGeneration` after TOTP enrollment. Copy the
codes to an approved offline store and securely remove the plaintext output. The portal accepts a
recovery code in its separate field; it never returns codes through an API response.

This local recovery workflow is not enterprise account recovery. Production needs verified help
desk procedures, identity-provider recovery, audit alerts, protected operator access and policy
for emergency revocation. Recovery does not authorize test execution or release decisions.
