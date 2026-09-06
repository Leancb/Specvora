[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\.."),
    [string]$Username = "leandro",
    [string]$EnrollmentOut = ".specvora-auth\mfa-enrollment.json",
    [switch]$ApproveEnrollment
)

$ErrorActionPreference = "Stop"
if (-not $ApproveEnrollment) {
    throw "Revise o usuario e use -ApproveEnrollment."
}
$root = [IO.Path]::GetFullPath($WorkspaceRoot)
$users = Join-Path $root ".specvora-auth\users.json"
$output = [IO.Path]::GetFullPath((Join-Path $root $EnrollmentOut))
if (-not (Test-Path -LiteralPath $users -PathType Leaf)) {
    throw "Arquivo de usuarios nao encontrado. Execute setup-portal-auth.ps1 primeiro."
}
& (Join-Path $root ".venv\Scripts\specvora-governance.exe") `
    --workspace-root $root enable-portal-mfa --users-file $users `
    --username $Username --enrollment-out $output
if ($LASTEXITCODE -ne 0) { throw "Falha ao habilitar MFA." }
Write-Host "Enrollment sensivel criado em: $output"
Write-Host "Importe o otpauth_uri no autenticador, valide o login e remova o arquivo com seguranca."
Write-Host "Sessoes anteriores deste usuario foram revogadas. Reinicie o portal se necessario."
