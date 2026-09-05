[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\.."),
    [string]$Repository = "Leancb/Specvora",
    [string]$Reviewer = "Leandro do Couto Brum",
    [switch]$ApproveUpload
)
$ErrorActionPreference="Stop"
if(-not $ApproveUpload){throw "Upload nao autorizado. Use -ApproveUpload apos revisar o pacote."}
$runtime=Join-Path ([IO.Path]::GetFullPath($WorkspaceRoot)) ".specvora-ci"
Get-Content (Join-Path $runtime "public-key.b64") -Raw |
    gh secret set SPECVORA_CI_PUBLIC_KEY_B64 --repo $Repository --env specvora-governed
if($LASTEXITCODE -ne 0){throw "Falha ao publicar chave publica."}
Get-Content (Join-Path $runtime "signed-approval.b64") -Raw |
    gh secret set SPECVORA_CI_SIGNED_APPROVAL_B64 --repo $Repository --env specvora-governed
if($LASTEXITCODE -ne 0){throw "Falha ao publicar aprovacao efemera."}
$Reviewer | gh variable set SPECVORA_CI_APPROVER --repo $Repository --env specvora-governed
if($LASTEXITCODE -ne 0){throw "Falha ao publicar identidade."}
Write-Host "Segredos publicados sem exibir valores. Dispare o workflow imediatamente."
