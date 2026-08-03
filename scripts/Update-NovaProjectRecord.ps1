[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ArchiveRoot = "",
    [string]$ProjectSnapshotPath = "",
    [string]$NextMilestone = "Milestone 77 - Local Project Record Daily-Use Validation."
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($NextMilestone)) {
    throw "NextMilestone must describe the exact next milestone."
}

function Get-Sha256 {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-TextSha256 {
    param([Parameter(Mandatory)][string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $algorithm.ComputeHash($bytes)
    }
    finally {
        $algorithm.Dispose()
    }
    return ([System.BitConverter]::ToString($hash) -replace '-', '').ToLowerInvariant()
}

function Get-RelativeArchivePath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Path
    )
    $normalizedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd("\") + "\"
    $normalizedPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $normalizedPath.StartsWith(
        $normalizedRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "The archive source is outside the configured root."
    }
    return $normalizedPath.Substring($normalizedRoot.Length).Replace("\", "/")
}

function Write-Utf8Atomic {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$StagingRoot
    )
    $temporary = Join-Path $StagingRoot ([System.IO.Path]::GetRandomFileName())
    [System.IO.File]::WriteAllText(
        $temporary,
        $Content,
        [System.Text.UTF8Encoding]::new($false)
    )
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Get-Category {
    param([Parameter(Mandatory)][string]$RelativePath)
    if ($RelativePath.StartsWith("Current/")) { return "current_status" }
    if ($RelativePath.StartsWith("Repository/")) { return "repository_snapshot" }
    if ($RelativePath.StartsWith("Sessions/")) { return "session" }
    if ($RelativePath.StartsWith("ChatGPT/Raw/")) { return "raw_chat_source" }
    if ($RelativePath.StartsWith("ChatGPT/Manifests/")) { return "import_manifest" }
    if ($RelativePath.StartsWith("Imported/")) { return "project_snapshot" }
    return "legacy_archive"
}

function Get-Authority {
    param([Parameter(Mandatory)][string]$Category)
    switch ($Category) {
        "current_status" { return "verified_runtime" }
        "repository_snapshot" { return "authoritative_repository" }
        "raw_chat_source" { return "raw_unapproved" }
        default { return "supporting_record" }
    }
}

$repository = (Resolve-Path -LiteralPath $RepositoryRoot).Path
if ([string]::IsNullOrWhiteSpace($ArchiveRoot)) {
    $novaRoot = Split-Path -Parent (Split-Path -Parent $repository)
    $ArchiveRoot = Join-Path $novaRoot "Archive"
}
$archive = [System.IO.Path]::GetFullPath($ArchiveRoot)
if ([System.IO.Path]::GetPathRoot($archive).TrimEnd("\") -ieq "C:") {
    throw "The NOVA project archive must not be written to C:. Use N:\Nova\Archive."
}

foreach ($directory in @(
    $archive,
    (Join-Path $archive "Current"),
    (Join-Path $archive "Sessions"),
    (Join-Path $archive "ChatGPT\Raw"),
    (Join-Path $archive "ChatGPT\Manifests"),
    (Join-Path $archive "Imported"),
    (Join-Path $archive "Repository")
)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

$staging = Join-Path $archive (".staging-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $staging | Out-Null

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 15
    $release = [string]$health.version
    if ($release -notmatch '^\d+\.\d+\.\d+$') {
        throw "The running NOVA version is not a release version."
    }

    $releaseCommit = (& git -C $repository rev-list -n 1 "v$release").Trim()
    if ($LASTEXITCODE -ne 0 -or $releaseCommit -notmatch '^[0-9a-f]{40}$') {
        throw "Git tag v$release is missing or invalid."
    }
    $originMain = (& git -C $repository rev-parse origin/main).Trim()
    if ($LASTEXITCODE -ne 0 -or $originMain -notmatch '^[0-9a-f]{40}$') {
        throw "The repository does not have a valid origin/main."
    }
    if ($originMain -ne $releaseCommit) {
        throw "origin/main and the installed release tag do not match. Project record refresh stopped."
    }

    $snapshotRoot = Join-Path $archive "Repository\v$release"
    if (-not (Test-Path -LiteralPath $snapshotRoot)) {
        $archiveZip = Join-Path $staging "repository.zip"
        & git -C $repository archive --format=zip --output=$archiveZip "v$release" `
            README.md SECURITY.md docs
        if ($LASTEXITCODE -ne 0) {
            throw "Git could not create the exact release documentation snapshot."
        }
        $snapshotStaging = Join-Path $staging "repository"
        Expand-Archive -LiteralPath $archiveZip -DestinationPath $snapshotStaging
        Move-Item -LiteralPath $snapshotStaging -Destination $snapshotRoot
    }

    if (-not [string]::IsNullOrWhiteSpace($ProjectSnapshotPath)) {
        $sourceSnapshot = (Resolve-Path -LiteralPath $ProjectSnapshotPath).Path
        $snapshotName = "ChatGPT-Project-Snapshot-" + (Get-Date -Format "yyyy-MM-dd")
        $snapshotDestination = Join-Path $archive "Imported\$snapshotName"
        if (-not (Test-Path -LiteralPath $snapshotDestination)) {
            Copy-Item -LiteralPath $sourceSnapshot -Destination $snapshotDestination -Recurse
        }
    }

    $knowledgeRoot = Join-Path (Split-Path -Parent $archive) "Memory"
    $knowledgeCount = @(
        Get-ChildItem -LiteralPath $knowledgeRoot -Recurse -File -ErrorAction SilentlyContinue
    ).Count
    $repositoryDocumentCount = @(
        Get-ChildItem -LiteralPath (Join-Path $snapshotRoot "docs") -File
    ).Count
    $rawChatCount = @(
        Get-ChildItem -LiteralPath (Join-Path $archive "ChatGPT\Raw") -File
    ).Count
    $capturedAt = (Get-Date).ToUniversalTime().ToString("o")
    $currentStatusPath = Join-Path $archive "Current\NOVA-Current-Status.md"
    $statusText = @"
# NOVA Current Project Status

Generated: $capturedAt

## Authoritative release

- Installed release: $release
- Git tag: v$release
- Release commit: $releaseCommit
- origin/main: $originMain
- Runtime health: $($health.status)
- Runtime environment: $($health.environment)

## Local project information

- Exact release repository documents: $repositoryDocumentCount files
- Approved local knowledge records: $knowledgeCount files
- Raw NOVA chat sources explicitly supplied: $rawChatCount files
- Existing development archives are indexed in place and are not overwritten.
- Runtime conversations remain in NOVA's local SQLite database and verified backups.

## Source priority

1. Current Git repository and release documentation.
2. Verified installed runtime and acceptance evidence.
3. Owner-approved checksum-bound knowledge.
4. Dated local project and session records.
5. Raw imported chat sources, which are evidence only and are not approved knowledge.

## Migration boundary

NOVA does not have automatic access to the owner's ChatGPT account. A ChatGPT
conversation is local only after the owner explicitly supplies that NOVA-only
source for guarded import. Unrelated chats, account exports, credentials, and
speculative discussion are not imported automatically.

## Exact next milestone

$NextMilestone
"@
    Write-Utf8Atomic -Path $currentStatusPath -Content $statusText -StagingRoot $staging

    $sessionDirectory = Join-Path $archive ("Sessions\" + (Get-Date -Format "yyyy"))
    New-Item -ItemType Directory -Path $sessionDirectory -Force | Out-Null
    $sessionPath = Join-Path $sessionDirectory (
        (Get-Date -Format "yyyy-MM-dd") + " - Local Project Record Migration.md"
    )
    if (-not (Test-Path -LiteralPath $sessionPath)) {
        $sessionText = @"
# Local Project Record Migration

Date: $(Get-Date -Format "yyyy-MM-dd")

The owner requested that NOVA project information be stored locally rather than
depend on ChatGPT chat history. NOVA created a canonical current-status record,
an exact Release $release documentation snapshot, a checksum-bound catalogue,
and guarded directories for explicitly supplied NOVA-only chat sources.

No unrelated chat, account export, credential, source file, approved knowledge,
or existing archive was deleted, overwritten, uploaded, or promoted automatically.
"@
        Write-Utf8Atomic -Path $sessionPath -Content $sessionText -StagingRoot $staging
    }

    $allowedExtensions = @(".html", ".json", ".md", ".txt", ".zip")
    $sources = @()
    foreach ($file in @(
        Get-ChildItem -LiteralPath $archive -Recurse -File |
            Where-Object {
                $_.Name -ne "archive-index.json" `
                    -and $allowedExtensions -contains $_.Extension.ToLowerInvariant() `
                    -and -not $_.FullName.StartsWith($staging, [System.StringComparison]::OrdinalIgnoreCase)
            }
    )) {
        $relativePath = Get-RelativeArchivePath -Root $archive -Path $file.FullName
        $category = Get-Category -RelativePath $relativePath
        $sha256 = Get-Sha256 -Path $file.FullName
        $pathHash = Get-TextSha256 -Text $relativePath
        $sources += [ordered]@{
            id = ($sha256.Substring(0, 12) + "-" + $pathHash.Substring(0, 8))
            label = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
            category = $category
            authority = Get-Authority -Category $category
            relative_path = $relativePath
            sha256 = $sha256
            size_bytes = [long]$file.Length
            captured_at = $capturedAt
        }
    }

    $migrationSummary = (
        "Authoritative repository and verified runtime information through Release " +
        "$release are indexed locally. Raw NOVA chat sources explicitly supplied: " +
        "$rawChatCount. ChatGPT conversations not explicitly supplied remain outside " +
        "this archive."
    )
    $index = [ordered]@{
        schema_version = 1
        generated_at = $capturedAt
        current_release = $release
        current_commit = $releaseCommit
        migration_summary = $migrationSummary
        sources = $sources
    }
    $indexJson = $index | ConvertTo-Json -Depth 8
    Write-Utf8Atomic -Path (Join-Path $archive "archive-index.json") `
        -Content $indexJson -StagingRoot $staging

    Write-Host "NOVA project record updated locally." -ForegroundColor Green
    Write-Host "Release: $release"
    Write-Host "Verified source entries prepared: $($sources.Count)"
    Write-Host "Raw NOVA chat sources supplied: $rawChatCount"
    Write-Host "Archive: $archive"
}
finally {
    if (Test-Path -LiteralPath $staging) {
        Remove-Item -LiteralPath $staging -Recurse -Force
    }
}
