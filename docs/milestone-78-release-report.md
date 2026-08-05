# Milestone 78 - Release 0.78.0 Candidate Report

**Status date:** 5 August 2026

**Status:** Candidate implementation and local verification complete

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

## Release boundary

This report does not claim 0.78.0 publication, installation, phone acceptance,
or protected-main integration. Those remain release gates after this candidate
is committed and reviewed.
