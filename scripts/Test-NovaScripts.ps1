[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Controller = Join-Path $PSScriptRoot "Nova.ps1"
$ProjectRecordControl = Join-Path $PSScriptRoot "Update-NovaProjectRecord.ps1"
$ProjectSourceImport = Join-Path $PSScriptRoot "Import-NovaProjectSource.ps1"
$tokens = $null
$parseErrors = $null

$controllerAst = [System.Management.Automation.Language.Parser]::ParseFile(
    $Controller,
    [ref]$tokens,
    [ref]$parseErrors
)

if ($parseErrors.Count -gt 0) {
    $messages = $parseErrors | ForEach-Object { $_.Message }
    throw "Nova.ps1 has syntax errors: $($messages -join '; ')"
}

foreach ($script in @($ProjectRecordControl, $ProjectSourceImport)) {
    $scriptTokens = $null
    $scriptErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $script,
        [ref]$scriptTokens,
        [ref]$scriptErrors
    ) | Out-Null
    if ($scriptErrors.Count -gt 0) {
        $messages = $scriptErrors | ForEach-Object { $_.Message }
        throw "$([System.IO.Path]::GetFileName($script)) has syntax errors: $($messages -join '; ')"
    }
}

$recordContent = Get-Content -Raw -LiteralPath $ProjectRecordControl
foreach ($requiredRecordControl in @(
    "N:\Nova\Archive",
    '[string]$ArchiveRoot = "N:\Nova\Archive"',
    "archive-index.json",
    "origin/main",
    "git -C",
    "Get-FileHash",
    "Raw NOVA chat sources explicitly supplied",
    "must not be written to C:",
    "NextMilestone",
    "Review the current roadmap and record the exact next approved milestone."
)) {
    if ($recordContent -notmatch [regex]::Escape($requiredRecordControl)) {
        throw "The project-record control is missing: $requiredRecordControl"
    }
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$bindingOutput = & powershell.exe `
    -NoLogo `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File $ProjectRecordControl `
    -ArchiveRoot "C:\NOVA-project-record-binding-test" 2>&1
$bindingExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($bindingExitCode -eq 0) {
    throw "The project-record control unexpectedly accepted an archive on C:."
}
if (($bindingOutput -join [Environment]::NewLine) -notmatch "must not be written to C:") {
    throw "The project-record launcher did not resolve its default repository path."
}
$global:LASTEXITCODE = 0

$importContent = Get-Content -Raw -LiteralPath $ProjectSourceImport
foreach ($requiredImportControl in @(
    "IMPORT NOVA SOURCE",
    "conversations.json",
    "25000000",
    ".partial",
    "Get-FileHash",
    "raw_unapproved_source",
    "Nothing was added to approved knowledge"
)) {
    if ($importContent -notmatch [regex]::Escape($requiredImportControl)) {
        throw "The project-source import control is missing: $requiredImportControl"
    }
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

foreach ($requiredIntegrityCheck in @(
    "Assert-NovaDatabaseIntegrity",
    "/api/v1/system/integrity",
    "TimeoutSec 35",
    "Active database: read-only integrity check passed."
)) {
    if ($controllerContent -notmatch [regex]::Escape($requiredIntegrityCheck)) {
        throw "Nova.ps1 does not verify the active database on demand: $requiredIntegrityCheck"
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
    "Phone Access On.cmd" = "phone-enable"
    "Phone Access Off.cmd" = "phone-disable"
    "Check Phone Access.cmd" = "phone-status"
}

foreach ($projectLauncher in @(
    "Update NOVA Project Record.cmd",
    "Import NOVA Source.cmd"
)) {
    $path = Join-Path $ProjectRoot $projectLauncher
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing project-record launcher: $projectLauncher"
    }
    $content = Get-Content -Raw -LiteralPath $path
    if ($content -notmatch 'scripts\\(Update-NovaProjectRecord|Import-NovaProjectSource)\.ps1') {
        throw "$projectLauncher does not call its guarded PowerShell control."
    }
}

$funnelFunction = $controllerAst.Find(
    {
        param($ast)
        $ast -is [System.Management.Automation.Language.FunctionDefinitionAst] `
            -and $ast.Name -eq "Test-NovaFunnelEnabled"
    },
    $true
)
if ($null -eq $funnelFunction) {
    throw "Nova.ps1 does not define its Funnel configuration check."
}
Invoke-Expression $funnelFunction.Extent.Text

$privateServeJson = @'
{"TCP":{"443":{"HTTPS":true}},"AllowFunnel":{"nova.example.ts.net:443":false}}
'@
$publicFunnelJson = @'
{"TCP":{"443":{"HTTPS":true}},"AllowFunnel":{"nova.example.ts.net:443":true}}
'@
$foregroundFunnelJson = @'
{"Foreground":{"session":{"AllowFunnel":{"nova.example.ts.net:443":true}}}}
'@
if (Test-NovaFunnelEnabled -Json "{}") {
    throw "An empty Tailscale configuration was incorrectly classified as public."
}
if (Test-NovaFunnelEnabled -Json $privateServeJson) {
    throw "A private Serve configuration was incorrectly classified as public."
}
if (-not (Test-NovaFunnelEnabled -Json $publicFunnelJson)) {
    throw "A public Funnel configuration was not detected."
}
if (-not (Test-NovaFunnelEnabled -Json $foregroundFunnelJson)) {
    throw "A foreground public Funnel configuration was not detected."
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

foreach ($requiredPhoneControl in @(
    "Enable-NovaPhoneAccess",
    "Disable-NovaPhoneAccess",
    "Show-NovaPhoneAccessStatus",
    "NOVA_TAILSCALE_DNS_NAME",
    "unexpected private DNS name",
    "http://127.0.0.1:5173",
    "funnel",
    "serve",
    "--bg",
    "--yes",
    "serve",
    "reset",
    "tailscale-serve.json",
    "another service",
    "FunnelEnabled",
    "CertDomains",
    "HTTPS certificates are not enabled",
    "/f/serve?node=",
    "Run as administrator",
    "Tls12",
    "TimeoutSeconds = 120",
    "No router port or public Funnel was opened."
)) {
    if ($controllerContent -notmatch [regex]::Escape($requiredPhoneControl)) {
        throw "Nova.ps1 does not preserve the private phone-access control: $requiredPhoneControl"
    }
}

Write-Host "Nova Windows scripts are structurally valid." -ForegroundColor Green
