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
$HealthUrl = "http://localhost:8000/api/v1/health"

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
    param([int]$TimeoutSeconds = 90)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2
            $page = Invoke-WebRequest -Uri $NovaUrl -UseBasicParsing -TimeoutSec 2
            if ($health.status -eq "ok" -and $page.StatusCode -eq 200) {
                return $health
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)

    Show-ContainerDiagnostics
    throw "Nova did not become ready within $TimeoutSeconds seconds. The recent container diagnostics are shown above."
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
    Write-Host ""
    Write-Host "Nova $($health.version) is ready at $NovaUrl" -ForegroundColor Green
    Write-Host "Your database and document folders remain local on this PC."
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
        Write-Host ""
        Write-Host "Nova $($health.version) is healthy at $NovaUrl" -ForegroundColor Green
    }
    catch {
        Write-Host ""
        Write-Host "Nova is not responding at $NovaUrl." -ForegroundColor Yellow
    }
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
