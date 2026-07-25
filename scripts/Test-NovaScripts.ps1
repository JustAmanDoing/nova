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

$ContainerEntrypoint = Join-Path $ProjectRoot "backend\docker-entrypoint.sh"
$entrypointBytes = [System.IO.File]::ReadAllBytes($ContainerEntrypoint)
$entrypointText = [System.Text.Encoding]::UTF8.GetString($entrypointBytes)
if (-not $entrypointText.StartsWith("#!/bin/sh`n")) {
    throw "backend/docker-entrypoint.sh must use an LF-terminated Linux shebang."
}
if ($entrypointText.Contains("`r`n")) {
    throw "backend/docker-entrypoint.sh contains CRLF line endings."
}

$controllerContent = Get-Content -Raw -LiteralPath $Controller
foreach ($requiredDiagnostic in @(
    "Show-ContainerDiagnostics",
    "docker compose logs",
    "--no-color",
    "--tail",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "TimeoutSeconds = 180",
    "lastFailure",
    "Last readiness check"
)) {
    if ($controllerContent -notmatch [regex]::Escape($requiredDiagnostic)) {
        throw "Nova.ps1 does not include bounded startup diagnostics: $requiredDiagnostic"
    }
}

foreach ($requiredVersionGuard in @(
    "Get-ExpectedNovaVersion",
    "Get-NovaVersionState",
    "backend\pyproject.toml",
    "Nova version mismatch",
    "Start Nova.cmd"
)) {
    if ($controllerContent -notmatch [regex]::Escape($requiredVersionGuard)) {
        throw "Nova.ps1 does not include the runtime version guard: $requiredVersionGuard"
    }
}

foreach ($requiredOperationalStatus in @(
    "Show-NovaOperationalStatus",
    "/api/v1/system/status",
    "storage_free_bytes",
    "storage_free_percent",
    "Needs attention:"
)) {
    if ($controllerContent -notmatch [regex]::Escape($requiredOperationalStatus)) {
        throw "Nova.ps1 does not surface operational status: $requiredOperationalStatus"
    }
}

foreach ($requiredUpdateBackupGuard in @(
    "New-NovaPreUpdateBackup",
    "/api/v1/backups",
    "X-Nova-Intent",
    "local-user-action",
    "pre-update backup failed",
    "backup.verified",
    "backup.sha256"
)) {
    if ($controllerContent -notmatch [regex]::Escape($requiredUpdateBackupGuard)) {
        throw "Nova.ps1 does not include the pre-update backup guard: $requiredUpdateBackupGuard"
    }
}

$updateFunctionIndex = $controllerContent.IndexOf("function Update-Nova")
$backupCallIndex = $controllerContent.IndexOf(
    "    New-NovaPreUpdateBackup",
    $updateFunctionIndex
)
$pullIndex = $controllerContent.IndexOf(
    "    & git pull --ff-only",
    $updateFunctionIndex
)
if (
    $updateFunctionIndex -lt 0 `
    -or $backupCallIndex -lt $updateFunctionIndex `
    -or $pullIndex -lt $backupCallIndex
) {
    throw "Update must create the safety backup before downloading source changes."
}

$backendProject = Get-Content -Raw -LiteralPath (
    Join-Path $ProjectRoot "backend\pyproject.toml"
)
$backendVersionMatch = [regex]::Match(
    $backendProject,
    '(?m)^version\s*=\s*"(?<version>[^"]+)"\s*$'
)
if (-not $backendVersionMatch.Success) {
    throw "backend/pyproject.toml does not declare the Nova version."
}
$expectedVersion = $backendVersionMatch.Groups["version"].Value

$backendConfig = Get-Content -Raw -LiteralPath (
    Join-Path $ProjectRoot "backend\app\core\config.py"
)
if ($backendConfig -notmatch [regex]::Escape("app_version: str = `"$expectedVersion`"")) {
    throw "The backend package and API versions do not match."
}

$frontendPackage = Get-Content -Raw -LiteralPath (
    Join-Path $ProjectRoot "frontend\package.json"
) | ConvertFrom-Json
if ($frontendPackage.version -ne $expectedVersion) {
    throw "The frontend and backend package versions do not match."
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
