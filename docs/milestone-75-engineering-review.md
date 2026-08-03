# Milestone 75 - Engineering Review

**Review date:** 3 August 2026

**Reviewed proposal:** Milestone 76 Local NOVA Project Record

**Decision:** Passed with implementation conditions

## Existing components to reuse

- Pydantic settings and storage-boundary validation;
- FastAPI route, schema, and domain-service separation;
- path-containment and SHA-256 patterns from approved knowledge;
- safe partial-resource reporting from backup inventory;
- existing same-origin frontend and responsive navigation;
- Windows PowerShell structural tests and typed-confirmation patterns;
- Git release documentation and exact-commit verification;
- local N-drive archive, source, knowledge, backup, and acceptance roots.

No external dependency is required.

## Proposed implementation shape

### Local archive layout

```text
N:\Nova\Archive\
|-- Current\NOVA-Current-Status.md
|-- Sessions\YYYY\YYYY-MM-DD - NOVA Session.md
|-- ChatGPT\Raw\
|-- ChatGPT\Manifests\
|-- Imported\
`-- archive-index.json
```

Existing archive files remain in place and are catalogued; they are not moved
or rewritten.

### Backend

- Add an `archive_path` setting with a non-overlap storage check.
- Add a `ProjectArchiveService` that builds a bounded read-only catalogue from
  the generated index and verifies referenced file size and SHA-256.
- Add `GET /api/v1/project-archive` and a bounded read-only document endpoint.
- Return safe per-item warnings for missing or changed sources.
- Never write to the archive from the web API in the first slice.

### Host controls

- Add a project-record refresh control that writes a new current-status file
  and index atomically after verifying repository and runtime evidence.
- Add a separate explicit import control that copies one selected NOVA-only
  source with no overwrite, calculates SHA-256, and appends a manifest entry.
- Reject a likely full-account ChatGPT export by default.
- Require the owner to type `IMPORT NOVA SOURCE` before the copy occurs.
- Put temporary work beneath `N:\Nova\Cache` or a supplied N-drive path.

### Frontend

- Add a read-only **Project record** destination.
- Show current release/commit/status first, then source coverage and recent
  session/import evidence.
- Use clear labels: **Authoritative**, **Verified runtime**, **Approved
  knowledge**, and **Raw imported source**.
- Do not render raw HTML. Display eligible text as escaped plain text.
- Keep details collapsed by default on phone and preserve 44-pixel controls.

## Required automated tests

1. Empty archive returns a valid empty catalogue.
2. Valid index returns deterministic source ordering.
3. File and index checksum matches are reported as verified.
4. Changed, missing, malformed, and unsupported sources are isolated.
5. Traversal and root-escape attempts are rejected.
6. Preview and source-size limits are enforced.
7. The API performs no writes.
8. Import requires explicit confirmation and a supported source.
9. Import refuses overwrite and detects duplicate SHA-256.
10. Full-account export indicators are rejected by default.
11. Import manifest uses UTC, byte size, SHA-256, source label, and local path.
12. Current-status refresh fails safely if repository or runtime evidence is
    inconsistent.
13. Project record works without Ollama.
14. PC and 390-pixel layouts remain keyboard and touch usable.
15. Backend lint, strict typing, tests, and coverage remain green.
16. Frontend lint, tests, typing, and production build remain green.
17. Windows controls, Compose, production runtime, integrity, loopback, private
    Serve, and Funnel-off checks remain green.
18. No raw archive or manifest containing local source data is tracked by Git.

## Failure and recovery behavior

- A failed refresh leaves the previous current-status file and index intact.
- A failed import leaves no partially named source or manifest entry.
- A source that changes after indexing is marked unverified; it is not silently
  trusted or removed.
- Existing files are never deleted or overwritten by refresh or import.
- Recovery uses the original raw source plus checksum manifest; no model output
  is required to reconstruct the catalogue.

## Engineering risks

| Risk | Control |
| --- | --- |
| “All information” is mistaken for all account data | Import only explicitly selected NOVA sources; reject full-account exports by default. |
| Stale chat claims outrank code | Display the repository and verified runtime as higher-priority sources. |
| Raw personal text leaks to Git | Keep archive outside the repository and add tracked-file hygiene tests. |
| Archive view becomes another knowledge store | Catalogue sources; do not promote or rewrite their content. |
| Large export degrades the app | Bound source size, file count, preview length, and parsing. |
| A changed file remains labelled verified | Recalculate SHA-256 on every catalogue read. |

## Review conclusion

The owner-requested slice is bounded, testable, and implementable without an
external dependency or an authority expansion. Implementation may proceed.
