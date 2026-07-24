# Nova Architecture Review — 25 July 2026

## Outcome

Nova's current modular monolith remains the right architecture for the intake
MVP. FastAPI, React, and SQLite provide clear boundaries without the operational
cost of microservices. The review found no reason to replace the stack or split
the application into additional services.

The system continues to satisfy the approved principles:

- Local-first and useful without an AI provider
- Read-only treatment of source files
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
Source files themselves are never changed.

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
- Recommendation, approval, execution, audit, and undo modules
- Chatbot and semantic retrieval

These are not required to complete the current Observe and Understand slice.

## Risks to monitor

1. Measure scan duration and database growth as the document set increases.
2. Introduce FTS5 when `LIKE` search latency becomes noticeable, rather than
   pre-emptively adding a second datastore.
3. Replace the current additive schema setup with ordered migration files before
   several more persisted features are introduced.
4. Define backup and recovery for the SQLite volume before Nova becomes the only
   index of a large document collection.
5. Review retention and redaction before storing sensitive document text.

## Next architectural gate

Proceed to recommendation work only after the current intake slice is tested
with representative local files and its failure states are acceptable. The
chatbot remains explicitly outside this review.
