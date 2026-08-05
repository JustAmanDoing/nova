# Milestone 78 - Releases 0.78.0 and 0.78.1 Report

**Status date:** 5 August 2026

**Status:** Release 0.78.0 published and installed; 0.78.1 control patch pending

## Scope

Release 0.78.0 adds the approved read-only Librarian MVP. It exposes local
knowledge health and evidence-backed review guidance without adding a database,
write API, autonomous action, external service, or AI dependency.

## Safety result

The API surface is GET-only. Automated coverage compares the database and every
knowledge file byte-for-byte before and after health, queue, and item-detail
requests. UI coverage confirms evidence inspection sends no mutation request.
All material changes remain in the existing owner-controlled review workflow.

## Verification record

- Backend Ruff passed.
- Backend strict mypy passed across 40 source files.
- The complete backend suite passed: 164 tests with 93.65% coverage.
- Frontend lint and type checking passed.
- The complete frontend suite passed: 55 tests across 5 files.
- The production frontend build passed and emitted `librarian.html`.
- Windows controller and launcher structural validation passed.
- Docker Compose configuration and complete backend/frontend image builds
  passed from the finished source.
- An isolated production runtime reported healthy version 0.78.0, served the
  Librarian page with no-cache behavior, returned matching direct and
  same-origin health results, exposed the empty-store 13-item deterministic
  review queue and item detail, ran the backend process as non-root UID 100,
  and preserved the database SHA-256 across all Librarian reads.
- Working-tree whitespace and repository-scope checks remain the final
  pre-commit gate.
- The installed 0.76.2 live stack remained running and healthy throughout;
  its active database passed the read-only integrity check.

## Protected integration and installed evidence

- PR #27 merged the reviewed candidate at
  `fc6509e884cdf0f009f88d329831680c569d8268` after all four checks passed.
- A fresh `main` run rebuilt and exercised the exact merge; all four jobs
  passed again.
- Release 0.78.0 was published from that merge and installed only after a
  verified pre-update database backup.
- The installed PC and private-phone endpoints both reported version 0.78.0
  and knowledge health 100.
- The installed queue contained four optional missing-coverage items and no
  duplicate, conflict, stale, missing-file, broken-reference, or checksum
  issue.
- Database and approved-knowledge SHA-256 values were unchanged across direct,
  same-origin, detail, Project Record, and private-phone reads.
- The Project Record was refreshed for 0.78.0 with 569 checksum-bound entries.

## Control patch

The release workflow exposed a Windows PowerShell parameter-binding defect in
the Project Record launcher. Release 0.78.1 moves default repository-path
resolution into the script body, adds a launcher regression check, and replaces
the stale default next-milestone label. It does not change Librarian behavior or
knowledge.

## Release boundary

Owner acceptance of the installed Librarian on PC and phone remains the final
Milestone 78 gate. No automatic knowledge action is authorized.
