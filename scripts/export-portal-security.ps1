[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\.."),
    [Parameter(Mandatory = $true)][string]$Endpoint,
    [Parameter(Mandatory = $true)][string]$AllowedHost,
    [string]$StateDb = ".specvora-auth\session-state.db",
    [string]$Checkpoint = ".specvora-auth\security-export-checkpoint.json",
    [int]$BatchSize = 100,
    [switch]$ApproveExport
)

$ErrorActionPreference = "Stop"
if (-not $ApproveExport) {
    throw "Revise endpoint e allowlist e use -ApproveExport."
}
if (-not $env:SPECVORA_SIEM_TOKEN) {
    $secure = Read-Host "SIEM runtime token" -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { $env:SPECVORA_SIEM_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}
$root = [IO.Path]::GetFullPath($WorkspaceRoot)
& (Join-Path $root ".venv\Scripts\specvora.exe") export-security `
    --workspace-root $root --state-db (Join-Path $root $StateDb) `
    --checkpoint (Join-Path $root $Checkpoint) --endpoint $Endpoint `
    --allowed-host $AllowedHost --batch-size $BatchSize
if ($LASTEXITCODE -ne 0) { throw "Falha ao exportar eventos de seguranca." }
Write-Host "O token foi mantido somente neste PowerShell."
