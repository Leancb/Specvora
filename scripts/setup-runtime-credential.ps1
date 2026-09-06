[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z][a-z0-9-]{1,62}$')]
    [string]$Alias,
    [switch]$ApproveSetup
)

$ErrorActionPreference = "Stop"
if (-not $ApproveSetup) {
    throw "Use -ApproveSetup para confirmar a configuracao somente neste PowerShell."
}

$first = Read-Host "Credential for $Alias" -AsSecureString
$second = Read-Host "Confirm credential" -AsSecureString
$firstPointer = [IntPtr]::Zero
$secondPointer = [IntPtr]::Zero
try {
    $firstPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($first)
    $secondPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($second)
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($firstPointer)
    $confirmation = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secondPointer)
    if ($plain -cne $confirmation) { throw "Credential confirmation does not match." }
    if ($plain.Length -lt 16 -or $plain.Length -gt 4096 -or $plain -match "[`r`n`0]") {
        throw "Credential must contain 16 to 4096 characters without control line breaks."
    }
    $variable = "SPECVORA_CREDENTIAL_" + $Alias.ToUpperInvariant().Replace("-", "_")
    [Environment]::SetEnvironmentVariable($variable, $plain, "Process")
    Write-Host "Credential reference '$Alias' is available only in this PowerShell process."
    Write-Host "The credential value was not displayed or written to disk."
} finally {
    if ($firstPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($firstPointer)
    }
    if ($secondPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secondPointer)
    }
    Remove-Variable plain, confirmation -ErrorAction SilentlyContinue
}
