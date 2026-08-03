[CmdletBinding()]
param(
    [string]$SourcePath = "",
    [string]$Label = "",
    [string]$Confirmation = "",
    [string]$ArchiveRoot = "N:\Nova\Archive"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    $SourcePath = Read-Host "Full path to one NOVA-only chat or project source"
}
$source = (Resolve-Path -LiteralPath $SourcePath).Path
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Select one source file, not a folder."
}

$extension = [System.IO.Path]::GetExtension($source).ToLowerInvariant()
$allowedExtensions = @(".html", ".json", ".md", ".txt", ".zip")
if ($allowedExtensions -notcontains $extension) {
    throw "Supported NOVA source types are .txt, .md, .json, .html, and .zip."
}
$sourceInfo = Get-Item -LiteralPath $source
if ($sourceInfo.Length -gt 25000000) {
    throw "This source exceeds the 25 MB bounded import limit. Split it into NOVA-only sources first."
}
if ($sourceInfo.Name -ieq "conversations.json") {
    throw "A full ChatGPT account conversation export is not imported by default. Supply one NOVA-only source instead."
}
if ($extension -eq ".zip") {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($source)
    try {
        $entryNames = @($zip.Entries | ForEach-Object { $_.FullName })
        if ($entryNames -contains "conversations.json") {
            throw "This appears to be a full ChatGPT account export. Extract and supply only the NOVA conversation source."
        }
    }
    finally {
        $zip.Dispose()
    }
}

if ([string]::IsNullOrWhiteSpace($Label)) {
    $Label = Read-Host "Short source label"
}
$Label = $Label.Trim()
if ([string]::IsNullOrWhiteSpace($Label) -or $Label.Length -gt 120) {
    throw "The source label must contain 1 to 120 characters."
}
if ([string]::IsNullOrWhiteSpace($Confirmation)) {
    $Confirmation = Read-Host "Type IMPORT NOVA SOURCE to preserve this file locally"
}
if ($Confirmation -cne "IMPORT NOVA SOURCE") {
    throw "Import cancelled. Nothing was copied."
}

$archive = [System.IO.Path]::GetFullPath($ArchiveRoot)
if ([System.IO.Path]::GetPathRoot($archive).TrimEnd("\") -ieq "C:") {
    throw "The NOVA project archive must not be written to C:."
}
$rawRoot = Join-Path $archive "ChatGPT\Raw"
$manifestRoot = Join-Path $archive "ChatGPT\Manifests"
New-Item -ItemType Directory -Path $rawRoot -Force | Out-Null
New-Item -ItemType Directory -Path $manifestRoot -Force | Out-Null

$sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
foreach ($manifestFile in @(
    Get-ChildItem -LiteralPath $manifestRoot -Filter "*.json" -File -ErrorAction SilentlyContinue
)) {
    try {
        $existing = Get-Content -Raw -LiteralPath $manifestFile.FullName | ConvertFrom-Json
        if ([string]$existing.sha256 -eq $sha256) {
            throw "This exact source is already preserved as $($existing.relative_path)."
        }
    }
    catch [System.ArgumentException] {
        throw "An existing import manifest is malformed: $($manifestFile.Name)."
    }
}

$safeLabel = ($Label -replace '[^A-Za-z0-9_-]+', '-').Trim('-')
if ([string]::IsNullOrWhiteSpace($safeLabel)) { $safeLabel = "nova-source" }
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmss.fffffffZ")
$destinationName = "$timestamp-$safeLabel-$($sha256.Substring(0, 12))$extension"
$destination = Join-Path $rawRoot $destinationName
if (Test-Path -LiteralPath $destination) {
    throw "The no-overwrite destination already exists."
}

$partial = "$destination.partial"
try {
    Copy-Item -LiteralPath $source -Destination $partial
    $copiedSha256 = (Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($copiedSha256 -ne $sha256) {
        throw "The copied source checksum does not match the original."
    }
    Move-Item -LiteralPath $partial -Destination $destination

    $normalizedRoot = [System.IO.Path]::GetFullPath($archive).TrimEnd("\") + "\"
    $normalizedDestination = [System.IO.Path]::GetFullPath($destination)
    if (-not $normalizedDestination.StartsWith(
        $normalizedRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "The copied source escaped the configured archive root."
    }
    $relativePath = $normalizedDestination.Substring($normalizedRoot.Length).Replace("\", "/")
    $manifest = [ordered]@{
        schema_version = 1
        label = $Label
        source_filename = $sourceInfo.Name
        relative_path = $relativePath
        size_bytes = [long]$sourceInfo.Length
        sha256 = $sha256
        imported_at = (Get-Date).ToUniversalTime().ToString("o")
        status = "raw_unapproved_source"
        limitation = "Preserved evidence only. Not approved knowledge and not automatically supplied to the model."
    }
    $manifestPath = Join-Path $manifestRoot "$timestamp-$safeLabel.json"
    [System.IO.File]::WriteAllText(
        $manifestPath,
        ($manifest | ConvertTo-Json -Depth 6),
        [System.Text.UTF8Encoding]::new($false)
    )

    & (Join-Path $PSScriptRoot "Update-NovaProjectRecord.ps1") `
        -RepositoryRoot (Split-Path -Parent $PSScriptRoot) `
        -ArchiveRoot $archive
    if ($LASTEXITCODE -ne 0) {
        throw "The source was preserved, but the project-record index refresh failed."
    }

    Write-Host "NOVA source preserved locally." -ForegroundColor Green
    Write-Host "Label: $Label"
    Write-Host "SHA-256: $sha256"
    Write-Host "Nothing was added to approved knowledge."
}
catch {
    if (Test-Path -LiteralPath $partial) {
        Remove-Item -LiteralPath $partial -Force
    }
    throw
}
