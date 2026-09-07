param(
    [ValidateSet("bootstrap", "rotate")]
    [string]$Command = "rotate",
    [Parameter(Mandatory = $true)][string]$DiscoveryEndpoint,
    [Parameter(Mandatory = $true)][string]$Issuer,
    [Parameter(Mandatory = $true)][string[]]$AllowedHost,
    [string]$Output = ".specvora-auth\oidc-jwks.json",
    [string]$WorkspaceRoot = "D:\Specvora",
    [switch]$ApproveTrustUpdate
)

$ErrorActionPreference = "Stop"
if (-not $ApproveTrustUpdate) {
    throw "OIDC trust update requires explicit -ApproveTrustUpdate."
}

$python = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Specvora virtual-environment Python was not found."
}

$arguments = @(
    "-m", "specvora.oidc_trust_cli", $Command,
    "--discovery-endpoint", $DiscoveryEndpoint,
    "--issuer", $Issuer,
    "--output", $Output,
    "--workspace-root", $WorkspaceRoot
)
foreach ($hostName in $AllowedHost) {
    $arguments += @("--allowed-host", $hostName)
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "OIDC trust update failed; the current trust file was preserved."
}
