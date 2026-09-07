param(
    [Parameter(Mandatory = $true)][string]$DiscoveryEndpoint,
    [Parameter(Mandatory = $true)][string]$Issuer,
    [Parameter(Mandatory = $true)][string[]]$AllowedHost,
    [string]$TrustFile = ".specvora-auth\oidc-jwks.json",
    [string]$AuditLog = ".specvora-auth\oidc-trust-audit.jsonl",
    [string]$WorkspaceRoot = "D:\Specvora"
)

$ErrorActionPreference = "Stop"
$python = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
$arguments = @(
    "-m", "specvora.oidc_monitor_cli",
    "--discovery-endpoint", $DiscoveryEndpoint, "--issuer", $Issuer,
    "--trust-file", $TrustFile, "--audit-log", $AuditLog,
    "--workspace-root", $WorkspaceRoot
)
foreach ($hostName in $AllowedHost) { $arguments += @("--allowed-host", $hostName) }
& $python @arguments
$monitorExit = $LASTEXITCODE
if ($monitorExit -eq 10) { throw "OIDC trust change requires independent human review." }
if ($monitorExit -eq 20) { throw "OIDC trust monitoring detected a blocking condition." }
if ($monitorExit -ne 0) { throw "OIDC trust monitoring failed." }
