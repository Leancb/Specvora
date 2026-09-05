[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\.."),
    [string]$Repository = "Leancb/Specvora",
    [string]$Reviewer = "Leandro do Couto Brum",
    [switch]$ApproveUpload
)
$ErrorActionPreference="Stop"
if(-not $ApproveUpload){throw "Upload nao autorizado. Use -ApproveUpload apos revisar o pacote."}
$root=[IO.Path]::GetFullPath($WorkspaceRoot)
$runtimeRoot=Join-Path $root ".specvora-ci"
$pointer=Join-Path $runtimeRoot "current-session.txt"
if(-not (Test-Path -LiteralPath $pointer -PathType Leaf)){
    throw "Nenhuma sessao preparada. Execute prepare-ci-approval.ps1 primeiro."
}
$sessionId=(Get-Content -LiteralPath $pointer -Raw).Trim()
if($sessionId -notmatch '^\d{8}-\d{6}-[0-9a-f]{8}$'){
    throw "Identificador de sessao invalido. Prepare uma nova autorizacao."
}
$runtime=Join-Path (Join-Path $runtimeRoot "sessions") $sessionId
$publicPath=Join-Path $runtime "public-key.b64"
$signedPath=Join-Path $runtime "signed-approval.b64"
if(-not (Test-Path -LiteralPath $publicPath -PathType Leaf) -or
   -not (Test-Path -LiteralPath $signedPath -PathType Leaf)){
    throw "Pacote da sessao esta incompleto. Prepare uma nova autorizacao."
}
try {
    $publicBytes=[Convert]::FromBase64String((Get-Content -LiteralPath $publicPath -Raw).Trim())
    $signedB64=(Get-Content -LiteralPath $signedPath -Raw).Trim()
    $signedJson=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($signedB64)) |
        ConvertFrom-Json
    $expiresAt=[DateTimeOffset]::Parse($signedJson.claims.expires_at)
} catch {
    throw "Pacote da sessao e invalido. Prepare uma nova autorizacao."
}
if($publicBytes.Length -ne 32){throw "Chave publica Ed25519 invalida."}
if($expiresAt -le [DateTimeOffset]::UtcNow){
    throw "Autorizacao expirada. Execute prepare-ci-approval.ps1 novamente."
}
Get-Content -LiteralPath $publicPath -Raw |
    gh secret set SPECVORA_CI_PUBLIC_KEY_B64 --repo $Repository --env specvora-governed
if($LASTEXITCODE -ne 0){throw "Falha ao publicar chave publica."}
Get-Content -LiteralPath $signedPath -Raw |
    gh secret set SPECVORA_CI_SIGNED_APPROVAL_B64 --repo $Repository --env specvora-governed
if($LASTEXITCODE -ne 0){throw "Falha ao publicar aprovacao efemera."}
$Reviewer | gh variable set SPECVORA_CI_APPROVER --repo $Repository --env specvora-governed
if($LASTEXITCODE -ne 0){throw "Falha ao publicar identidade."}
Write-Host "Sessao $sessionId publicada sem exibir valores. Dispare o workflow imediatamente."
