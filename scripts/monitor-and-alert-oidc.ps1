param(
    [Parameter(Mandatory = $true)][string]$DiscoveryEndpoint,
    [Parameter(Mandatory = $true)][string]$Issuer,
    [Parameter(Mandatory = $true)][string[]]$ProviderAllowedHost,
    [Parameter(Mandatory = $true)][string]$AlertEndpoint,
    [Parameter(Mandatory = $true)][string[]]$AlertAllowedHost,
    [Parameter(Mandatory = $true)][string]$ReportFile,
    [string]$TrustFile = ".specvora-auth\oidc-jwks.json",
    [string]$AuditLog = ".specvora-auth\oidc-trust-audit.jsonl",
    [string]$WorkspaceRoot = "D:\Specvora"
)

$ErrorActionPreference = "Stop"
if (-not $env:SPECVORA_OIDC_ALERT_TOKEN) {
    throw "SPECVORA_OIDC_ALERT_TOKEN is required in the current process environment."
}
$python = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
$monitorArguments = @(
    "-m", "specvora.oidc_monitor_cli",
    "--discovery-endpoint", $DiscoveryEndpoint, "--issuer", $Issuer,
    "--trust-file", $TrustFile, "--audit-log", $AuditLog,
    "--workspace-root", $WorkspaceRoot, "--output", $ReportFile
)
foreach ($hostName in $ProviderAllowedHost) {
    $monitorArguments += @("--allowed-host", $hostName)
}
& $python @monitorArguments
$monitorExit = $LASTEXITCODE
if ($monitorExit -notin @(0, 10, 20)) { throw "OIDC monitoring failed." }
$alertArguments = @(
    "-m", "specvora.oidc_alert_cli", "--report", $ReportFile,
    "--endpoint", $AlertEndpoint, "--workspace-root", $WorkspaceRoot
)
foreach ($hostName in $AlertAllowedHost) { $alertArguments += @("--allowed-host", $hostName) }
& $python @alertArguments
if ($LASTEXITCODE -ne 0) { throw "OIDC alert delivery failed." }
