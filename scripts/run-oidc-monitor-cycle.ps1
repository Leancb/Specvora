param(
    [string]$ConfigurationFile,
    [string]$DiscoveryEndpoint,
    [string]$Issuer,
    [string[]]$ProviderAllowedHost,
    [string]$TrustFile,
    [string]$AuditLog,
    [string]$AlertEndpoint,
    [string[]]$AlertAllowedHost,
    [string]$WorkspaceRoot
)
$ErrorActionPreference = "Stop"
if ($ConfigurationFile) {
    $configuration = Import-PowerShellDataFile -LiteralPath $ConfigurationFile
    & $PSCommandPath @configuration
    exit $LASTEXITCODE
}
if (-not $DiscoveryEndpoint -or -not $Issuer -or -not $ProviderAllowedHost -or
    -not $TrustFile -or -not $AuditLog -or -not $AlertEndpoint -or
    -not $AlertAllowedHost -or -not $WorkspaceRoot) {
    throw "Forneca a configuracao OIDC completa ou use -ConfigurationFile."
}
if (-not $env:SPECVORA_OIDC_ALERT_TOKEN) {
    throw "Defina SPECVORA_OIDC_ALERT_TOKEN apenas no ambiente de execucao."
}
$providerArguments = @()
foreach ($hostName in $ProviderAllowedHost) {
    $providerArguments += @("--provider-allowed-host", $hostName)
}
$alertArguments = @()
foreach ($hostName in $AlertAllowedHost) {
    $alertArguments += @("--alert-allowed-host", $hostName)
}
& specvora-oidc-cycle `
    --discovery-endpoint $DiscoveryEndpoint `
    --issuer $Issuer `
    @providerArguments `
    --trust-file $TrustFile `
    --audit-log $AuditLog `
    --alert-endpoint $AlertEndpoint `
    @alertArguments `
    --state-database "state\oidc-monitor.db" `
    --workspace-root $WorkspaceRoot
if ($LASTEXITCODE -ne 0) { throw "O ciclo monitorado OIDC falhou." }
