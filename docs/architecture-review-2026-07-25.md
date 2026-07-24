# Nova Architecture Review — 25 July 2026

## Outcome

Nova's current modular monolith remains the right architecture for the intake
MVP. FastAPI, React, and SQLite provide clear boundaries without the operational
cost of microservices. The review found no reason to replace the stack or split
the application into additional services.

The system continues to satisfy the approved principles:

- Local-first and useful without an AI provider
- Source changes only through explicit, approved, reversible actions
- Explainable understanding results
- Minimal infrastructure
- Versioned API boundaries
- Automated validation

## Corrections completed

### Background resilience

A failed scan is now logged without terminating the background watcher. An
unexpected parser exception is isolated to the affected file and becomes a safe,
structured `extractor_error` result. Internal exception details remain in local
logs rather than being exposed through the API.

### Resource bounds

Source-file size and expanded extracted-text size now have independent limits.
PDF extraction stops as the configured output boundary is reached. DOCX
processing checks the uncompressed XML member before loading it and also bounds
the extracted text. This reduces memory-exhaustion and compressed-document risk.

### Inventory integrity

Each scan now reconciles SQLite with the current intake folder. Records for
removed source files are deleted from the derived inventory, and remaining exact
duplicates are re-evaluated so a valid canonical record is always selected.
The scanner itself never changes source files.

### Reporting accuracy

Dashboard totals now use a dedicated unfiltered summary endpoint. Searching or
filtering the visible table no longer changes the overall inventory metrics.
Search requests are lightly delayed to avoid unnecessary requests while typing.
Existing understanding records are backfilled automatically when a newer schema
requires searchable text or extraction metadata, even when the source file has
not changed.

### Boundary consistency

Health responses now use the configuration attached to the running FastAPI
application, including test or alternate local configurations. File candidates
whose resolved path escapes the configured intake root are ignored.

### Deterministic recommendation boundary

The first Recommend slice remains inside the modular monolith. Versioned,
deterministic rules consume normalized understanding records and persist either
an explainable suggestion or an explicit insufficient-evidence outcome.
Recommendations are invalidated when content, understanding, duplicate status,
or rules change. Recommendation and review code cannot invoke execution.

### Approval boundary

Approval is implemented as version-bound review state, not as permission to
execute a file operation. Approve, edit, reject, ignore, and review-again
actions update only local SQLite state. Edited filenames and destinations are
validated before storage. When a recommendation changes, the earlier review is
treated as stale and the file returns to the queue.

### Execution, audit, and undo boundary

Execution is a separate endpoint and user confirmation. It accepts only a
current approved recommendation for a non-duplicate file, revalidates safe
relative paths, refuses existing destinations, and re-fingerprints the source.
Nova copies with exclusive destination creation, verifies the destination and
source SHA-256 values, and only then removes the source.

Each move or undo commits an append-only `started` event before touching the
filesystem and a terminal `succeeded` or `failed` event afterward. Undo is
available only while the filed copy matches the recorded fingerprint and the
original intake path is empty. This implements the prior architectural gate as
one unit rather than introducing an unsafe move-only shortcut.

## Deliberately retained

- **SQLite and SQL `LIKE` search:** appropriate for the current single-user MVP
  and small document set.
- **Single deployable backend:** easier to test, run, and recover locally than a
  collection of services.
- **Synchronous scan transaction:** preserves a simple consistent inventory at
  current scale.
- **Full extracted text in local SQLite:** enables offline search while API
  responses expose only previews and evidence.

## Deferred until evidence justifies it

- SQLite FTS5 or a separate search index
- Background job queues or a message bus
- Microservices
- OCR
- Chatbot and semantic retrieval

These are not required to complete the current guarded intake workflow.

## Risks to monitor

1. Measure scan duration and database growth as the document set increases.
2. Introduce FTS5 when `LIKE` search latency becomes noticeable, rather than
   pre-emptively adding a second datastore.
3. Replace the current additive schema setup with ordered migration files before
   several more persisted features are introduced.
4. Define backup and recovery for the SQLite volume before Nova becomes the only
   index of a large document collection.
5. Review retention and redaction before storing sensitive document text.
6. Surface and manually reconcile any operation left in `started` state after
   an unexpected process or host interruption.

## Next architectural gate

Exercise move and undo locally with representative TXT, Markdown, PDF, and DOCX
files before introducing learning or automation. Measure failure cases and keep
all automatic filing disabled. The next implementation choice should be local
OCR or learning from confirmed approvals; the chatbot remains explicitly
outside this review.
