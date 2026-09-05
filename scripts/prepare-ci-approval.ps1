[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\.."),
    [string]$Reviewer = "Leandro do Couto Brum",
    [string]$PrivateKey = "$env:USERPROFILE\.specvora\keys\local-20260904-private.key",
    [string]$PublicKey = "$env:USERPROFILE\.specvora\keys\local-20260904-public.key",
    [switch]$ApproveSigning
)

$ErrorActionPreference = "Stop"
if (-not $ApproveSigning) { throw "Revise ci/module22-plan e use -ApproveSigning." }
$root = [IO.Path]::GetFullPath($WorkspaceRoot)
$runtime = Join-Path $root ".specvora-ci"
[IO.Directory]::CreateDirectory($runtime) | Out-Null
$utf8 = New-Object Text.UTF8Encoding($false)
$requestPath = Join-Path $runtime "request.json"
$actionPath = Join-Path $runtime "action.json"
$claimsPath = Join-Path $runtime "claims.json"
$signedPath = Join-Path $runtime "signed-approval.json"
$request = [ordered]@{
    project_id="petstore-demo"; signed_approval=$null; workspace_root=$root
    generated_dir=(Join-Path $root "ci\module22-plan")
    report_path=(Join-Path $root "ci\evidence\pytest-report.json")
    base_url="http://127.0.0.1:8080"; allowed_hosts=@("127.0.0.1")
    approval="APPROVED"; timeout_seconds=60
}
[IO.File]::WriteAllText($requestPath,($request|ConvertTo-Json -Depth 8),$utf8)
$env:SPECVORA_ACTION_PATH_MODE="workspace-relative"
& (Join-Path $root ".venv\Scripts\specvora-governance.exe") --workspace-root $root `
    prepare-execution $requestPath --kind api --output $actionPath
if($LASTEXITCODE -ne 0){throw "Falha ao preparar acao portavel."}
$issued=[DateTimeOffset]::UtcNow
$claims=[ordered]@{
    version="specvora-approval-v1"; approval_id=[guid]::NewGuid().ToString()
    project_id="petstore-demo"; purpose="api-execution"; reviewer=$Reviewer
    artifact_sha256=(Get-FileHash $actionPath -Algorithm SHA256).Hash.ToLowerInvariant()
    issued_at=$issued.ToString("o"); expires_at=$issued.AddMinutes(30).ToString("o")
}
[IO.File]::WriteAllText($claimsPath,($claims|ConvertTo-Json -Depth 8),$utf8)
& (Join-Path $root ".venv\Scripts\specvora-governance.exe") --workspace-root $root `
    sign $claimsPath --artifact $actionPath --private-key $PrivateKey `
    --approval APPROVED_SIGNING --output $signedPath
if($LASTEXITCODE -ne 0){throw "Falha ao assinar acao portavel."}
[IO.File]::WriteAllText((Join-Path $runtime "public-key.b64"),
    [Convert]::ToBase64String([IO.File]::ReadAllBytes($PublicKey)),$utf8)
[IO.File]::WriteAllText((Join-Path $runtime "signed-approval.b64"),
    [Convert]::ToBase64String([IO.File]::ReadAllBytes($signedPath)),$utf8)
Write-Host "Pacote efemero criado em $runtime e valido por 30 minutos."
Write-Host "A chave privada nao foi copiada. Proximo: scripts/publish-ci-approval.ps1."
