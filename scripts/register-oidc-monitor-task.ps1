param(
    [Parameter(Mandatory=$true)][string]$CycleScript,
    [Parameter(Mandatory=$true)][string]$ArgumentFile,
    [ValidateRange(5,1440)][int]$IntervalMinutes = 15,
    [switch]$ApproveTaskRegistration
)
$ErrorActionPreference = "Stop"
if (-not $ApproveTaskRegistration) {
    throw "Use -ApproveTaskRegistration para registrar a tarefa local explicitamente."
}
$resolvedScript = (Resolve-Path -LiteralPath $CycleScript).Path
$resolvedArguments = (Resolve-Path -LiteralPath $ArgumentFile).Path
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument (
    "-NoProfile -NonInteractive -File `"$resolvedScript`" -ConfigurationFile `"$resolvedArguments`""
)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "Specvora-OIDC-Monitor" -Action $action `
    -Trigger $trigger -Settings $settings -Description "Read-only Specvora OIDC trust monitoring" `
    -Force | Out-Null
Write-Host "Tarefa Specvora-OIDC-Monitor registrada; nenhuma rotacao foi autorizada."
