[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

<#
RETIRED COMPATIBILITY SENTINEL

This file remains temporarily so older Windows checkouts and structural tests
fail clearly instead of silently using the former GitHub-first status design.
It must not read, calculate, publish, or validate NOVA's current project status.

Retired implementation markers retained only for compatibility detection:
- project-status
- STATUS.md
- integrated_commit
- active_commit
- /git/ref/heads/
- /pulls/
#>

throw @"
CURRENT STATUS NOT VERIFIED

scripts/Test-NovaContinuity.ps1 is retired and cannot determine where NOVA is
up to. Read the exact Google Drive document named 'NOVA Handoff'. That document
is NOVA's only authoritative project-status and cross-device continuity record.
GitHub may be used only to verify supporting code, release, test, commit, and
technical-history evidence.
"@
