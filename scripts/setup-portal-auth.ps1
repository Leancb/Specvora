[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\.."),
    [string]$Username = "leandro",
    [string]$DisplayName = "Leandro do Couto Brum",
    [string[]]$Roles = @("reviewer", "operator"),
    [switch]$ApproveSetup
)

$ErrorActionPreference = "Stop"
if (-not $ApproveSetup) {
    throw "Revise usuario e papeis e use -ApproveSetup."
}
$root = [IO.Path]::GetFullPath($WorkspaceRoot)
$auth = Join-Path $root ".specvora-auth"
$users = Join-Path $auth "users.json"
$sessionKey = Join-Path $auth "session.key"
[IO.Directory]::CreateDirectory($auth) | Out-Null
if (-not (Test-Path -LiteralPath $sessionKey -PathType Leaf)) {
    $bytes = [byte[]]::new(32)
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    } finally {
        $generator.Dispose()
    }
    [IO.File]::WriteAllBytes($sessionKey, $bytes)
    Write-Host "Nova chave de sessao criada; ela nao sera exibida."
}
$userExists = $false
if (Test-Path -LiteralPath $users -PathType Leaf) {
    $userExists = @((Get-Content -LiteralPath $users -Raw | ConvertFrom-Json).users | `
        Where-Object { $_.username -eq $Username }).Count -gt 0
}
if (-not $userExists) {
    $arguments = @(
        "--workspace-root", $root, "create-portal-user",
        "--users-file", $users, "--username", $Username, "--display-name", $DisplayName
    )
    foreach ($role in $Roles) { $arguments += @("--role", $role) }
    & (Join-Path $root ".venv\Scripts\specvora-governance.exe") @arguments
    if ($LASTEXITCODE -ne 0) { throw "Falha ao criar usuario do portal." }
} else {
    Write-Host "Usuario existente preservado: $Username"
}
$env:SPECVORA_PORTAL_AUTH_MODE = "required"
$env:SPECVORA_PORTAL_USERS_FILE = $users
$env:SPECVORA_PORTAL_SESSION_KEY = $sessionKey
$env:SPECVORA_PORTAL_STATE_DB = Join-Path $auth "session-state.db"
$env:SPECVORA_PORTAL_SESSION_MINUTES = "30"
$env:SPECVORA_PORTAL_COOKIE_SECURE = "false"
Write-Host "Autenticacao aplicada somente a este PowerShell."
Write-Host "Inicie o portal em 127.0.0.1; para HTTPS, habilite cookie seguro."
