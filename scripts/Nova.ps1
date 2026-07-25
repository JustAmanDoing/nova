[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "status", "update")]
    [string]$Action = "start",

    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$NovaUrl = "http://localhost:5173"
$DashboardProbeUrl = "http://127.0.0.1:5173"
$HealthUrl = "http://127.0.0.1:8000/api/v1/health"
$SystemStatusUrl = "http://127.0.0.1:8000/api/v1/system/status"
$DatabaseIntegrityUrl = "http://127.0.0.1:8000/api/v1/system/integrity"
$BackupUrl = "http://127.0.0.1:8000/api/v1/backups"
$BackendProjectFile = Join-Path $ProjectRoot "backend\pyproject.toml"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "Nova: $Message" -ForegroundColor Cyan
}

function Assert-Command {
    param(
        [string]$Name,
        [string]$Guidance
    )
    if ($null -eq (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is not installed. $Guidance"
    }
}

function Assert-Docker {
    Assert-Command "docker" "Install and start Docker Desktop, then try again."
    & docker compose version *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose is unavailable. Update Docker Desktop, then try again."
    }
    & docker info --format "{{.ServerVersion}}" *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Desktop is installed but not running. Start it, then try again."
    }
}

function Get-ExpectedNovaVersion {
    if (-not (Test-Path -LiteralPath $BackendProjectFile -PathType Leaf)) {
        throw "Nova cannot find backend\pyproject.toml, so it cannot verify the application version."
    }
    $projectContent = Get-Content -Raw -LiteralPath $BackendProjectFile
    $versionMatch = [regex]::Match(
        $projectContent,
        '(?m)^version\s*=\s*"(?<version>[^"]+)"\s*$'
    )
    if (-not $versionMatch.Success) {
        throw "Nova cannot read the expected application version from backend\pyproject.toml."
    }
    return $versionMatch.Groups["version"].Value
}

function Get-NovaVersionState {
    param([object]$Health)

    $runningVersion = [string]$Health.version
    if ([string]::IsNullOrWhiteSpace($runningVersion)) {
        throw "Nova's health response did not include an application version."
    }
    $expectedVersion = Get-ExpectedNovaVersion
    return [PSCustomObject]@{
        Expected = $expectedVersion
        Running = $runningVersion
        Matches = $runningVersion -eq $expectedVersion
    }
}

function New-NovaPreUpdateBackup {
    try {
        $health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 3
        if ($health.status -ne "ok") {
            throw "The health endpoint did not report an okay status."
        }
    }
    catch {
        Write-Step "Nova is not running, so no live pre-update backup was created"
        Write-Host "The update will continue. Start Nova before a future update if you want an automatic safety snapshot." -ForegroundColor Yellow
        return
    }

    Write-Step "Creating a verified pre-update database backup"
    try {
        $backup = Invoke-RestMethod `
            -Uri $BackupUrl `
            -Method Post `
            -Headers @{ "X-Nova-Intent" = "local-user-action" } `
            -TimeoutSec 30
    }
    catch {
        throw "Nova is running, but its pre-update backup failed. The update stopped before downloading source changes. $($_.Exception.Message)"
    }

    if (
        -not $backup.verified `
        -or [string]::IsNullOrWhiteSpace([string]$backup.sha256) `
        -or [string]::IsNullOrWhiteSpace([string]$backup.filename)
    ) {
        throw "Nova did not confirm a verified pre-update backup. The update stopped before downloading source changes."
    }

    Write-Host "Verified backup: $($backup.filename)" -ForegroundColor Green
    Write-Host "SHA-256: $($backup.sha256)"
}

function Show-NovaOperationalStatus {
    try {
        $status = Invoke-RestMethod -Uri $SystemStatusUrl -TimeoutSec 3
    }
    catch {
        Write-Host "Nova could not read operational measurements." -ForegroundColor Yellow
        return
    }

    if ($null -ne $status.storage_free_bytes -and $null -ne $status.storage_free_percent) {
        $freeGigabytes = [math]::Round(
            [double]$status.storage_free_bytes / 1GB,
            1
        )
        $freePercent = [math]::Round(
            [double]$status.storage_free_percent,
            1
        )
        Write-Host "Local storage: $freeGigabytes GB free ($freePercent%)."
    }

    if ($status.warnings.Count -eq 0) {
        Write-Host "Nova reports no operational warnings." -ForegroundColor Green
        return
    }

    foreach ($warning in $status.warnings) {
        Write-Host "Needs attention: $warning" -ForegroundColor Yellow
    }
}

function Assert-NovaDatabaseIntegrity {
    Write-Step "Checking the active database"
    try {
        $integrity = Invoke-RestMethod `
            -Uri $DatabaseIntegrityUrl `
            -TimeoutSec 35
    }
    catch {
        throw "Nova could not complete the active database integrity check. $($_.Exception.Message)"
    }

    if ($integrity.status -ne "ok") {
        $detail = [string]$integrity.detail
        if ([string]::IsNullOrWhiteSpace($detail)) {
            $detail = "The active database did not pass its integrity check."
        }
        throw $detail
    }

    Write-Host "Active database: read-only integrity check passed." -ForegroundColor Green
}

function Invoke-Compose {
    param([string[]]$Arguments)
    & docker compose @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed while running: docker compose $($Arguments -join ' ')"
    }
}

function Show-ContainerDiagnostics {
    param([int]$TailLines = 80)

    Write-Step "Showing recent container diagnostics"
    & docker compose ps
    & docker compose logs --no-color --tail $TailLines
}

function Wait-ForNova {
    param([int]$TimeoutSeconds = 180)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastFailure = "No readiness response was received."
    do {
        try {
            $health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2
            $page = Invoke-WebRequest -Uri $DashboardProbeUrl -UseBasicParsing -TimeoutSec 2
            if ($health.status -eq "ok" -and $page.StatusCode -eq 200) {
                return $health
            }
            $lastFailure = "API status was '$($health.status)' and dashboard status was '$($page.StatusCode)'."
        }
        catch {
            $lastFailure = $_.Exception.Message
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    Show-ContainerDiagnostics
    throw "Nova did not become ready within $TimeoutSeconds seconds. Last readiness check: $lastFailure The recent container diagnostics are shown above."
}

function Start-Nova {
    Assert-Docker
    Write-Step "Building and starting the local application"
    try {
        Invoke-Compose @("up", "--build", "-d")
    }
    catch {
        Show-ContainerDiagnostics
        throw
    }
    Write-Step "Waiting for the dashboard and API"
    $health = Wait-ForNova
    $versionState = Get-NovaVersionState -Health $health
    if (-not $versionState.Matches) {
        throw "Nova version mismatch: this folder contains $($versionState.Expected), but the running application is $($versionState.Running). Run Start Nova.cmd again to rebuild from this folder."
    }
    Write-Host ""
    Write-Host "Nova $($health.version) is ready at $NovaUrl" -ForegroundColor Green
    Write-Host "Your database and document folders remain local on this PC."
    Show-NovaOperationalStatus
    if (-not $NoBrowser) {
        Start-Process $NovaUrl
    }
}

function Stop-Nova {
    Assert-Docker
    Write-Step "Stopping the application"
    Invoke-Compose @("down")
    Write-Host ""
    Write-Host "Nova is stopped. Its database and document files were retained." -ForegroundColor Green
}

function Show-NovaStatus {
    Assert-Docker
    Write-Step "Checking containers"
    Invoke-Compose @("ps")
    try {
        $health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 3
    }
    catch {
        Write-Host ""
        Write-Host "Nova is not responding at $NovaUrl." -ForegroundColor Yellow
        return
    }

    $versionState = Get-NovaVersionState -Health $health
    Write-Host ""
    if ($versionState.Matches) {
        Write-Host "Nova $($health.version) is healthy at $NovaUrl" -ForegroundColor Green
    }
    else {
        Write-Host "Nova is healthy at $NovaUrl, but its version is out of date." -ForegroundColor Yellow
        Write-Host "Version mismatch: this folder contains $($versionState.Expected), but the running application is $($versionState.Running)." -ForegroundColor Yellow
        Write-Host "Double-click Start Nova.cmd to rebuild Nova from the current folder." -ForegroundColor Yellow
    }
    Show-NovaOperationalStatus
    Assert-NovaDatabaseIntegrity
}

function Update-Nova {
    Assert-Command "git" "Install Git for Windows, then try again."
    Assert-Docker
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".git"))) {
        throw "This Nova folder is not a Git checkout, so it cannot update itself."
    }
    $changes = & git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw "Git could not inspect the Nova folder."
    }
    if ($changes) {
        throw "Nova has local changes. Update stopped so none of your work is overwritten."
    }
    New-NovaPreUpdateBackup
    Write-Step "Downloading the latest approved source"
    & git pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        throw "Git could not apply a fast-forward update. No local files were overwritten."
    }
    Start-Nova
}

Push-Location $ProjectRoot
try {
    switch ($Action) {
        "start" { Start-Nova }
        "stop" { Stop-Nova }
        "status" { Show-NovaStatus }
        "update" { Update-Nova }
    }
}
catch {
    Write-Host ""
    Write-Host "Nova could not complete this request." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}
