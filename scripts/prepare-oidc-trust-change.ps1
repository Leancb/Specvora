param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$DiscoveryEndpoint,
    [Parameter(Mandatory = $true)][string]$Issuer,
    [Parameter(Mandatory = $true)][string[]]$AllowedHost,
    [Parameter(Mandatory = $true)][string]$Reviewer,
    [string]$TrustFile = ".specvora-auth\oidc-jwks.json",
    [string]$Proposal = ".specvora-auth\changes\oidc-trust-proposal.json",
    [string]$Claims = ".specvora-auth\changes\oidc-trust-claims.json",
    [string]$WorkspaceRoot = "D:\Specvora",
    [switch]$Bootstrap,
    [switch]$ApproveDiscovery
)

$ErrorActionPreference = "Stop"
if (-not $ApproveDiscovery) { throw "Trust discovery requires explicit -ApproveDiscovery." }
$python = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
$arguments = @(
    "-m", "specvora.oidc_trust_approval_cli", "--workspace-root", $WorkspaceRoot,
    "propose", "--project-id", $ProjectId, "--discovery-endpoint", $DiscoveryEndpoint,
    "--issuer", $Issuer, "--proposal", $Proposal, "--trust-file", $TrustFile
)
foreach ($hostName in $AllowedHost) { $arguments += @("--allowed-host", $hostName) }
if ($Bootstrap) { $arguments += "--bootstrap" }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "OIDC trust proposal failed." }
& $python -m specvora.oidc_trust_approval_cli --workspace-root $WorkspaceRoot `
    prepare-approval --proposal $Proposal --reviewer $Reviewer --output $Claims
if ($LASTEXITCODE -ne 0) { throw "OIDC trust approval preparation failed." }
Write-Host "Sign the claims offline with purpose oidc-trust-change and the exact proposal artifact."
