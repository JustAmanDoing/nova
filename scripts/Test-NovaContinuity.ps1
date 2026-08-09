[CmdletBinding()]
param(
    [string]$Repository = "JustAmanDoing/nova",
    [string]$StatusRef = "project-status",
    [string]$StatusPath = "STATUS.md"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ApiRoot = "https://api.github.com/repos/$Repository"
$Headers = @{
    Accept = "application/vnd.github+json"
    "User-Agent" = "NOVA-Continuity-Check"
    "X-GitHub-Api-Version" = "2022-11-28"
}

function Stop-Unverified {
    param([Parameter(Mandatory)][string]$Reason)

    Write-Error "CURRENT STATUS NOT VERIFIED: $Reason"
}

function Invoke-GitHubRead {
    param([Parameter(Mandatory)][string]$Uri)

    try {
        return Invoke-RestMethod -Uri $Uri -Headers $Headers -Method Get -TimeoutSec 30
    } catch {
        Stop-Unverified "GitHub evidence could not be read ($Uri): $($_.Exception.Message)"
    }
}

function Get-StatusField {
    param(
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$Name
    )

    $match = [regex]::Match(
        $Content,
        "(?m)^$([regex]::Escape($Name)):\s*(?<value>.+?)\s*$"
    )
    if (-not $match.Success) {
        Stop-Unverified "Canonical status field '$Name' is missing."
    }
    return $match.Groups["value"].Value
}

function Get-BranchHead {
    param([Parameter(Mandatory)][string]$Branch)

    $escapedBranch = [uri]::EscapeDataString($Branch)
    $reference = Invoke-GitHubRead "$ApiRoot/git/ref/heads/$escapedBranch"
    return [string]$reference.object.sha
}

try {
    $escapedPath = ($StatusPath -split "/" | ForEach-Object {
        [uri]::EscapeDataString($_)
    }) -join "/"
    $escapedRef = [uri]::EscapeDataString($StatusRef)
    $statusResponse = Invoke-GitHubRead (
        "$ApiRoot/contents/$escapedPath" + "?ref=$escapedRef"
    )
    if ([string]$statusResponse.encoding -ne "base64") {
        Stop-Unverified "Canonical status content was not returned as base64."
    }

    $statusBytes = [Convert]::FromBase64String(
        ([string]$statusResponse.content -replace "\s", "")
    )
    $status = [Text.Encoding]::UTF8.GetString($statusBytes)

    foreach ($heading in @(
        "## Verification state",
        "## Current milestone",
        "## Completed work",
        "## Checks and tests",
        "## Branch and commit",
        "## Pull request and release state",
        "## Blockers and risks",
        "## Exact next action"
    )) {
        if (-not $status.Contains($heading)) {
            Stop-Unverified "Canonical status section '$heading' is missing."
        }
    }

    $verification = Get-StatusField $status "verification"
    if ($verification -ne "VERIFIED") {
        Stop-Unverified "Canonical status is marked '$verification'."
    }

    $recordVersion = Get-StatusField $status "record_version"
    if ($recordVersion -ne "1") {
        Stop-Unverified "Unsupported canonical status version '$recordVersion'."
    }

    $verifiedAt = Get-StatusField $status "verified_at"
    $parsedVerifiedAt = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse($verifiedAt, [ref]$parsedVerifiedAt)) {
        Stop-Unverified "Canonical verification timestamp is invalid."
    }

    $integratedBranch = Get-StatusField $status "integrated_branch"
    $integratedCommit = Get-StatusField $status "integrated_commit"
    $activeBranch = Get-StatusField $status "active_branch"
    $activeCommit = Get-StatusField $status "active_commit"
    $pullRequest = Get-StatusField $status "pull_request"

    foreach ($commit in @($integratedCommit, $activeCommit)) {
        if ($commit -notmatch "^[0-9a-f]{40}$") {
            Stop-Unverified "Canonical commit '$commit' is not a full SHA-1."
        }
    }

    $remoteIntegratedCommit = Get-BranchHead $integratedBranch
    if ($remoteIntegratedCommit -ne $integratedCommit) {
        Stop-Unverified (
            "Integrated branch '$integratedBranch' is $remoteIntegratedCommit, " +
            "not recorded commit $integratedCommit."
        )
    }

    $remoteActiveCommit = Get-BranchHead $activeBranch
    if ($remoteActiveCommit -ne $activeCommit) {
        Stop-Unverified (
            "Active branch '$activeBranch' is $remoteActiveCommit, " +
            "not recorded commit $activeCommit."
        )
    }

    if ($pullRequest -ne "none") {
        $pullRequestNumber = 0
        if (-not [int]::TryParse($pullRequest, [ref]$pullRequestNumber)) {
            Stop-Unverified "Pull request '$pullRequest' is not 'none' or a number."
        }
        $pr = Invoke-GitHubRead "$ApiRoot/pulls/$pullRequestNumber"
        if ([string]$pr.state -ne "open") {
            Stop-Unverified "Pull request #$pullRequestNumber is not open."
        }
        if ([string]$pr.base.ref -ne $integratedBranch) {
            Stop-Unverified "Pull request #$pullRequestNumber has an unexpected base."
        }
        if ([string]$pr.head.ref -ne $activeBranch) {
            Stop-Unverified "Pull request #$pullRequestNumber has an unexpected head."
        }
        if ([string]$pr.head.sha -ne $activeCommit) {
            Stop-Unverified "Pull request #$pullRequestNumber is not at the recorded head."
        }
    }

    Write-Host "NOVA canonical status is verified against GitHub." -ForegroundColor Green
    Write-Host "Milestone: $(Get-StatusField $status 'current_milestone')"
    Write-Host "Integrated: $integratedBranch@$integratedCommit"
    Write-Host "Active: $activeBranch@$activeCommit"
    Write-Host "Pull request: $pullRequest"
    Write-Host "Verified at: $verifiedAt"
} catch {
    if ($_.Exception.Message -like "*CURRENT STATUS NOT VERIFIED*") {
        throw
    }
    Stop-Unverified $_.Exception.Message
}
