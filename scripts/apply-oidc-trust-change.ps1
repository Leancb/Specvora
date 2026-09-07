param(
    [Parameter(Mandatory = $true)][string]$Proposal,
    [Parameter(Mandatory = $true)][string]$Approval,
    [Parameter(Mandatory = $true)][string]$PublicKey,
    [Parameter(Mandatory = $true)][string]$Operator,
    [string]$TrustFile = ".specvora-auth\oidc-jwks.json",
    [string]$Ledger = ".specvora-auth\oidc-trust-approvals.db",
    [string]$AuditLog = ".specvora-auth\oidc-trust-audit.jsonl",
    [string]$WorkspaceRoot = "D:\Specvora",
    [switch]$ApproveApplication
)

$ErrorActionPreference = "Stop"
if (-not $ApproveApplication) { throw "Trust application requires -ApproveApplication." }
$python = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
& $python -m specvora.oidc_trust_approval_cli --workspace-root $WorkspaceRoot apply `
    --proposal $Proposal --approval $Approval --public-key $PublicKey --trust-file $TrustFile `
    --ledger $Ledger --audit-log $AuditLog --operator $Operator
if ($LASTEXITCODE -ne 0) { throw "Approved OIDC trust change was not applied." }
