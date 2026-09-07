[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\.."),
    [string]$Username = "leandro",
    [string]$Output = ".specvora-auth\recovery-codes.json",
    [switch]$ApproveGeneration
)

$ErrorActionPreference = "Stop"
if (-not $ApproveGeneration) {
    throw "Revise o usuario e use -ApproveGeneration. Os codigos serao exibidos uma unica vez."
}
$root = [IO.Path]::GetFullPath($WorkspaceRoot)
$users = Join-Path $root ".specvora-auth\users.json"
$state = Join-Path $root ".specvora-auth\session-state.db"
$target = [IO.Path]::GetFullPath((Join-Path $root $Output))
if (-not (Test-Path -LiteralPath $users -PathType Leaf)) {
    throw "Arquivo de usuarios nao encontrado. Execute setup-portal-auth.ps1 primeiro."
}
$env:SPECVORA_PORTAL_STATE_BACKEND = "sqlite"
$env:SPECVORA_PORTAL_STATE_DB = $state
& (Join-Path $root ".venv\Scripts\specvora-governance.exe") `
    --workspace-root $root generate-portal-recovery --users-file $users `
    --username $Username --output $target
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar codigos de recuperacao." }
Write-Host "Codigos sensiveis criados em: $target"
Write-Host "Guarde-os offline e remova o arquivo com seguranca depois da copia."
Write-Host "Gerar um novo conjunto invalida todos os codigos anteriores."
