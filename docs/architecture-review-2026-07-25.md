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

### Interrupted-operation visibility

Nova now treats a non-terminal operation older than the configured safety delay
as an item for inspection. A read-only assessor resolves the recorded paths
within the intake and library boundaries, fingerprints any files found, and
classifies the current state. It can distinguish an unchanged source that is
safe to retry, a verified destination that likely completed without its final
audit event, two verified copies, conflicting content, missing files, unsafe
paths, and unreadable storage.

The dashboard surfaces the assessment and manual-review guidance. Nova does not
automatically delete a duplicate copy, synthesize a success event, retry an
action, or otherwise mutate recovery state. This closes the visibility gap
without weakening the explicit execution boundary.

### Backup and local network boundary

Nova now creates database snapshots through SQLite's online backup API, so a
snapshot remains transactionally consistent while the app is running in WAL
mode. A backup is published only after SQLite integrity verification succeeds.
Each snapshot has a unique timestamped name and a SHA-256 sidecar; earlier
backups are neither overwritten nor removed automatically.

Backups live under the host-mounted `data/backups` folder rather than only
inside the Docker database volume. This keeps them available if the application
volume is lost. Because snapshots contain extracted text, recommendations,
reviews, and audit events, they must be treated as sensitive local data.

The Docker Compose ports now bind to `127.0.0.1`. This matches the approved
no-remote-access default and prevents an unauthenticated Nova API from being
published to the local network.

### Guarded restore boundary

Restore now uses the same process-wide operation lock as scans, reviews, file
execution, undo, and backup creation. This prevents the live SQLite database
from being replaced while another Nova operation is using it. Restore accepts
only a backup whose recorded SHA-256 and SQLite integrity check both pass, and
the API requires an exact per-file confirmation phrase.

Before replacement, Nova creates a new verified safety snapshot of the current
database. The selected backup is copied to a temporary file and verified again
before atomic replacement. Nova then runs schema initialization, reconciles the
derived intake inventory with files currently on disk, and verifies SQLite
integrity. Any failure after replacement triggers automatic rollback from the
safety snapshot. Restore outcomes are written outside the database to a local
append-only JSONL record so replacing the database cannot erase the restore
event itself.

This feature restores database state only. It never treats a database snapshot
as authority to move, delete, recreate, or overwrite document files.

### Ordered schema migration boundary

Database initialization now uses a contiguous migration registry instead of
re-running one growing schema script and ad hoc column checks at every startup.
Each migration has an immutable version and name, is recorded only after its
work succeeds, and runs within a SQLite savepoint.

Nova can adopt databases created before the migration registry was introduced:
the historical steps are idempotent and preserve existing rows while filling
in missing tables, indexes, and columns. Startup refuses a schema version newer
than the running build and refuses recorded migration names that conflict with
the local registry. Restore uses the same migration runner before reconciling
the restored inventory, so older verified snapshots remain upgradeable.

### Bounded local OCR boundary

OCR remains part of the Understanding stage and cannot approve or execute a
file action. Supported image files are passed to a local Tesseract process.
PDFs continue to use their text layer first and invoke OCR only when that layer
is empty. Poppler renders scanned PDF pages into a private temporary directory;
temporary images are removed when extraction finishes.

OCR uses argument-list subprocess calls with no shell, fixed local executables,
an overall timeout, a page limit, a maximum rendered dimension, a temporary
rendered-byte limit, and the existing source and extracted-text limits. Missing
tools, timeouts, page-limit failures, render failures, and OCR process failures
become structured public diagnostics without exposing process output.

Existing image records previously marked unsupported and empty PDFs previously
processed only by `pypdf` are reconsidered once after OCR becomes available.
Successful or empty OCR results are then cached normally. Docker provides the
English Tesseract data and Poppler tools; OCR can be disabled explicitly.

### Confirmed preference-learning boundary

Nova may now adjust a future destination suggestion from successful historical
moves, but the learning surface is intentionally narrow. A learning example is
created only after a user-approved move completes and only when the user kept
Nova's category unchanged. Failed actions, reviews without execution, category
corrections, and duplicate event handling do not create examples.

A destination requires at least three active supporting moves and at least a
75% share among the matching document-type and category group. A tie produces
no learned preference. Undo invalidates its linked example, advances the
group-specific learning revision, and refreshes affected cached suggestions.
Unrelated document groups are not invalidated.

The preference changes only a suggested destination and is explained in the
recommendation. It cannot approve or execute an action. The existing explicit
approval, separate confirmation, containment, collision, and fingerprint
checks remain unchanged.

Learning is derived and user-controlled. Nova exposes grouped active and
reverted example counts without source content. An exact typed confirmation is
required to forget a group. Reset deletes the derived examples transactionally,
advances only that group's revision, refreshes affected recommendations, and
records a minimal local audit event. Files and file-action history are not
changed.

## Deliberately retained

- **SQLite and SQL `LIKE` search:** appropriate for the current single-user MVP
  and small document set. Nova applies deterministic per-field relevance
  weights, multi-term AND matching, and quoted phrases within this boundary.
- **Single deployable backend:** easier to test, run, and recover locally than a
  collection of services.
- **Narrow container initialization:** a startup wrapper creates and assigns
  only Nova's mounted storage directories, then immediately runs the API as the
  unprivileged `nova` account. This avoids both host-specific bind-mount
  failures and a root application process.
- **Synchronous scan transaction:** preserves a simple consistent inventory at
  current scale.
- **Full extracted text in local SQLite:** enables offline search while API
  responses expose only previews and evidence.

## Deferred until evidence justifies it

- SQLite FTS5 or a separate search index
- Background job queues or a message bus
- Microservices
- Chatbot and semantic retrieval

These are not required to complete the current guarded intake workflow.

## Risks to monitor

1. Measure scan duration and database growth as the document set increases.
2. Measure ranked `LIKE` search latency and introduce FTS5 only when it becomes
   noticeable, rather than pre-emptively adding a second datastore.
3. Keep every future persisted feature behind a new ordered migration and test
   both upgrade and rollback behavior.
4. Exercise verified backup and restore regularly with representative local
   data and preserve at least one independent copy of important backups.
5. Review retention and redaction before storing sensitive document text.
6. Define an explicitly approved reconciliation workflow only after real
   interrupted-operation cases demonstrate which recovery actions are needed.

## Next architectural gate

Exercise move, undo, OCR, backup, restore, and learned-destination refresh
locally with representative TXT, Markdown, PDF, DOCX, and image files. Measure
failure cases and keep all automatic filing disabled. Semantic search and
user-controlled automation require separate evidence and review; the chatbot
remains explicitly outside this review.
