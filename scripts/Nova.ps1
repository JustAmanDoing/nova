[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet(
        "start",
        "stop",
        "status",
        "update",
        "phone-enable",
        "phone-disable",
        "phone-status"
    )]
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
$EnvironmentFile = Join-Path $ProjectRoot ".env"
$PhoneAccessStateDirectory = Join-Path $ProjectRoot "data\phone-access"
$PhoneAccessStateFile = Join-Path (
    $PhoneAccessStateDirectory
) "tailscale-serve.json"
$PhoneProxyTarget = "http://127.0.0.1:5173"

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

function Get-TailscaleExecutable {
    $command = Get-Command "tailscale.exe" -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $installedPath = Join-Path $env:ProgramFiles "Tailscale\tailscale.exe"
    if (Test-Path -LiteralPath $installedPath -PathType Leaf) {
        return $installedPath
    }

    throw "Tailscale is not installed. Install and connect Tailscale, then try again."
}

function Invoke-Tailscale {
    param(
        [string]$Executable,
        [string[]]$Arguments
    )

    $output = & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Tailscale could not complete: tailscale $($Arguments -join ' ')"
    }
    return ($output -join [Environment]::NewLine)
}

function ConvertTo-NovaCanonicalJson {
    param([string]$Json)

    if ([string]::IsNullOrWhiteSpace($Json)) {
        throw "Tailscale returned an empty configuration response."
    }
    return (
        $Json |
            ConvertFrom-Json |
            ConvertTo-Json -Depth 20 -Compress
    )
}

function Get-NovaTailscaleState {
    param([string]$Executable)

    $statusJson = Invoke-Tailscale -Executable $Executable -Arguments @(
        "status",
        "--json"
    )
    $status = $statusJson | ConvertFrom-Json
    if (-not $status.Self.Online) {
        throw "Tailscale is installed but this PC is not connected."
    }

    $dnsName = ([string]$status.Self.DNSName).TrimEnd(".")
    if ([string]::IsNullOrWhiteSpace($dnsName)) {
        throw "Tailscale did not provide a private DNS name for this PC."
    }
    if ($dnsName -notmatch '^[a-z0-9-]+(\.[a-z0-9-]+)*\.ts\.net$') {
        throw "Tailscale returned an unexpected private DNS name. Phone access stopped before changing NOVA."
    }

    return [PSCustomObject]@{
        DnsName = $dnsName
        ServeJson = ConvertTo-NovaCanonicalJson (
            Invoke-Tailscale -Executable $Executable -Arguments @(
                "serve",
                "status",
                "--json"
            )
        )
        FunnelJson = ConvertTo-NovaCanonicalJson (
            Invoke-Tailscale -Executable $Executable -Arguments @(
                "funnel",
                "status",
                "--json"
            )
        )
    }
}

function Set-NovaEnvironmentValue {
    param(
        [string]$Name,
        [string]$Value
    )

    $lines = @()
    if (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf) {
        $lines = @(Get-Content -LiteralPath $EnvironmentFile)
    }

    $replacement = "$Name=$Value"
    $matched = $false
    for ($index = 0; $index -lt $lines.Count; $index += 1) {
        if ($lines[$index] -match "^$([regex]::Escape($Name))=") {
            $lines[$index] = $replacement
            $matched = $true
        }
    }
    if (-not $matched) {
        $lines += $replacement
    }

    $temporaryPath = "$EnvironmentFile.tmp"
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines(
        $temporaryPath,
        [string[]]$lines,
        $utf8WithoutBom
    )
    Move-Item -LiteralPath $temporaryPath -Destination $EnvironmentFile -Force
}

function Test-NovaPhoneEndpoint {
    param(
        [string]$DnsName,
        [int]$TimeoutSeconds = 45
    )

    $phoneHealthUrl = "https://$DnsName/api/v1/health"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastFailure = "No HTTPS response was received."
    do {
        try {
            $health = Invoke-RestMethod -Uri $phoneHealthUrl -TimeoutSec 5
            if ($health.status -eq "ok") {
                return $health
            }
            $lastFailure = "The private endpoint returned '$($health.status)'."
        }
        catch {
            $lastFailure = $_.Exception.Message
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw "NOVA's private HTTPS endpoint did not become ready. $lastFailure"
}

function Enable-NovaPhoneAccess {
    Assert-Docker
    $tailscale = Get-TailscaleExecutable
    $state = Get-NovaTailscaleState -Executable $tailscale

    if ($state.FunnelJson -ne "{}") {
        throw "Tailscale Funnel is configured. NOVA will not enable phone access while a public Funnel exists."
    }

    if ($state.ServeJson -ne "{}") {
        if (-not (Test-Path -LiteralPath $PhoneAccessStateFile -PathType Leaf)) {
            throw "A Tailscale Serve configuration already exists and was not created by NOVA. Phone access stopped without changing it."
        }
        $recorded = ConvertTo-NovaCanonicalJson (
            Get-Content -Raw -LiteralPath $PhoneAccessStateFile
        )
        if ($recorded -ne $state.ServeJson) {
            throw "Tailscale Serve changed after NOVA recorded it. Phone access stopped without replacing another service."
        }
        $health = Test-NovaPhoneEndpoint -DnsName $state.DnsName
        Write-Host ""
        Write-Host "NOVA $($health.version) phone access is already on." -ForegroundColor Green
        Write-Host "Private address: https://$($state.DnsName)"
        return
    }

    Write-Step "Configuring NOVA's exact private phone address"
    Set-NovaEnvironmentValue `
        -Name "NOVA_TAILSCALE_DNS_NAME" `
        -Value $state.DnsName

    Write-Step "Applying the same-origin private gateway"
    try {
        Invoke-Compose @("up", "--build", "-d", "frontend")
    }
    catch {
        Show-ContainerDiagnostics
        throw
    }
    $null = Wait-ForNova

    Write-Step "Enabling private Tailscale HTTPS"
    $null = Invoke-Tailscale -Executable $tailscale -Arguments @(
        "serve",
        "--bg",
        "--yes",
        $PhoneProxyTarget
    )

    $enabledState = Get-NovaTailscaleState -Executable $tailscale
    if ($enabledState.FunnelJson -ne "{}") {
        $null = Invoke-Tailscale -Executable $tailscale -Arguments @(
            "serve",
            "reset"
        )
        throw "A public Funnel appeared while phone access was enabled. NOVA removed its Serve configuration and stopped."
    }
    if (
        $enabledState.ServeJson -eq "{}" `
        -or $enabledState.ServeJson -notmatch [regex]::Escape($PhoneProxyTarget)
    ) {
        throw "Tailscale did not confirm NOVA's expected private proxy."
    }

    New-Item -ItemType Directory -Force -Path (
        $PhoneAccessStateDirectory
    ) | Out-Null
    $enabledState.ServeJson | Set-Content `
        -LiteralPath $PhoneAccessStateFile `
        -Encoding UTF8

    $health = Test-NovaPhoneEndpoint -DnsName $enabledState.DnsName
    Write-Host ""
    Write-Host "NOVA $($health.version) is ready on your private Tailscale network." -ForegroundColor Green
    Write-Host "Phone address: https://$($enabledState.DnsName)"
    Write-Host "No router port or public Funnel was opened."
}

function Disable-NovaPhoneAccess {
    $tailscale = Get-TailscaleExecutable
    $state = Get-NovaTailscaleState -Executable $tailscale

    if ($state.ServeJson -eq "{}") {
        Write-Host "NOVA phone access is already off." -ForegroundColor Green
        return
    }
    if (-not (Test-Path -LiteralPath $PhoneAccessStateFile -PathType Leaf)) {
        throw "The active Tailscale Serve configuration was not recorded by NOVA. Disable stopped without changing it."
    }

    $recorded = ConvertTo-NovaCanonicalJson (
        Get-Content -Raw -LiteralPath $PhoneAccessStateFile
    )
    if ($recorded -ne $state.ServeJson) {
        throw "Tailscale Serve changed after NOVA recorded it. Disable stopped so another service is not removed."
    }

    Write-Step "Disabling NOVA's private phone address"
    $null = Invoke-Tailscale -Executable $tailscale -Arguments @(
        "serve",
        "reset"
    )
    $disabledState = Get-NovaTailscaleState -Executable $tailscale
    if ($disabledState.ServeJson -ne "{}") {
        throw "Tailscale still reports an active Serve configuration."
    }

    Remove-Item -LiteralPath $PhoneAccessStateFile -Force
    Write-Host ""
    Write-Host "NOVA phone access is off. Local desktop access is unchanged." -ForegroundColor Green
}

function Show-NovaPhoneAccessStatus {
    $tailscale = Get-TailscaleExecutable
    $state = Get-NovaTailscaleState -Executable $tailscale

    Write-Host ""
    Write-Host "Private device name: $($state.DnsName)"
    if ($state.FunnelJson -ne "{}") {
        Write-Host "Warning: a public Tailscale Funnel is configured." -ForegroundColor Red
    }
    else {
        Write-Host "Public Funnel: off" -ForegroundColor Green
    }

    if ($state.ServeJson -eq "{}") {
        Write-Host "NOVA phone access: off" -ForegroundColor Yellow
        return
    }
    if (-not (Test-Path -LiteralPath $PhoneAccessStateFile -PathType Leaf)) {
        Write-Host "NOVA phone access: unknown Serve configuration" -ForegroundColor Yellow
        return
    }

    $recorded = ConvertTo-NovaCanonicalJson (
        Get-Content -Raw -LiteralPath $PhoneAccessStateFile
    )
    if ($recorded -ne $state.ServeJson) {
        Write-Host "NOVA phone access: configuration changed; no automatic action taken" -ForegroundColor Yellow
        return
    }

    $health = Test-NovaPhoneEndpoint -DnsName $state.DnsName -TimeoutSeconds 10
    Write-Host "NOVA phone access: on and healthy (version $($health.version))" -ForegroundColor Green
    Write-Host "Private address: https://$($state.DnsName)"
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
        "phone-enable" { Enable-NovaPhoneAccess }
        "phone-disable" { Disable-NovaPhoneAccess }
        "phone-status" { Show-NovaPhoneAccessStatus }
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
