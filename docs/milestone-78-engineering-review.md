# Milestone 78 - The Librarian Engineering Review

**Decision date:** 5 August 2026

**Status:** Approved and implemented as a release candidate

## Service contract

`LibrarianService` is created beside Knowledge, Intake, Chat, Focus, and Project
Archive during application startup. It opens SQLite in read-only mode and reads
the existing knowledge root without writing files.

The API is GET-only:

- `GET /api/v1/librarian/health`
- `GET /api/v1/librarian/review`
- `GET /api/v1/librarian/item/{id}`

No mutation header, approval endpoint, ignore endpoint, scheduler, or database
migration is added.

## Deterministic analysis

- Duplicate analysis reuses the same exact-content and token-overlap score used
  during current knowledge approval, with the existing 0.8 threshold.
- Conflict analysis requires identical normalized titles and distinct normalized
  contents across verified active records.
- Stale and missing coverage reuse the published knowledge-quality checklist and
  its review intervals.
- Missing, broken, and checksum analysis resolves each approved active path
  inside the configured knowledge root and compares SHA-256 in constant time.
- Source confidence is the original stored candidate confidence; the Librarian
  does not generate another confidence value for the source.

## Health score

The overall store score is the unweighted mean of five visible dimensions:
existing core coverage, freshness, deterministic retrieval, file integrity, and
consistency. Consistency is the percentage of verified active records not
involved in a deterministic duplicate or structural conflict. Empty integrity
and consistency dimensions pass because there is no invalid source, while
missing coverage still keeps an empty knowledge store from appearing complete.

## Frontend

`librarian.html` adds the approved first-class navigation destination between
Record and Intake. The responsive page presents the store score, dimension
breakdown, issue counts, review queue, evidence, source confidence, verification
state, and immutable revision detail. Its only material link opens the existing
Chat knowledge review workflow. Item detail also exposes the existing
append-only record lifecycle events without creating another audit log.

## Required verification

- Backend Ruff, strict mypy, complete pytest suite, and coverage threshold
- Duplicate, conflict, stale, missing-file, broken-reference, checksum, item,
  API, and byte-for-byte read-only tests
- Frontend lint, type checking, tests, and production build
- Windows control validation
- Docker Compose configuration and representative production runtime checks
- Working-tree whitespace and repository-scope checks
