[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Controller = Join-Path $PSScriptRoot "Nova.ps1"
$tokens = $null
$parseErrors = $null

[System.Management.Automation.Language.Parser]::ParseFile(
    $Controller,
    [ref]$tokens,
    [ref]$parseErrors
) | Out-Null

if ($parseErrors.Count -gt 0) {
    $messages = $parseErrors | ForEach-Object { $_.Message }
    throw "Nova.ps1 has syntax errors: $($messages -join '; ')"
}

$launchers = @{
    "Start Nova.cmd" = "start"
    "Stop Nova.cmd" = "stop"
    "Check Nova.cmd" = "status"
    "Update Nova.cmd" = "update"
}

foreach ($launcher in $launchers.GetEnumerator()) {
    $path = Join-Path $ProjectRoot $launcher.Key
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing Windows launcher: $($launcher.Key)"
    }
    $content = Get-Content -Raw -LiteralPath $path
    if ($content -notmatch 'scripts\\Nova\.ps1') {
        throw "$($launcher.Key) does not call the shared Nova controller."
    }
    if ($content -notmatch "\s$($launcher.Value)(\s|$)") {
        throw "$($launcher.Key) does not request the $($launcher.Value) action."
    }
}

Write-Host "Nova Windows scripts are structurally valid." -ForegroundColor Green
