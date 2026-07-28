# Nova Architecture

## Purpose

Nova is a local-first personal assistant platform. The MVP proves one safe,
useful workflow before autonomy is introduced:

```text
Observe → Understand → Recommend → Approve → Execute → Audit → Learn
```

**Observe**, **Understand**, deterministic **Recommend**, explicit **Approve**,
guarded **Execute**, append-only **Audit**, and conservative destination
**Learn** are active today. Nova changes a file only through a separate
confirmed action that passes current-approval, path, conflict, and fingerprint
checks.

Local chat is an optional parallel interface:

```text
React chat page
  └── versioned FastAPI chat endpoints
        ├── local SQLite conversation history
        ├── deterministic knowledge proposal detector
        │     └── pending owner review
        │           ├── reject → no permanent record
        │           └── approve → SQLite record + local Markdown copy
        └── Nova-owned provider adapter
              └── Ollama on the Windows host
```

It does not bypass or extend the guarded file workflow.

## Current vertical slice

```text
Local data/intake folder
  └── periodic or manual scan
        └── metadata + SHA-256 fingerprint
              └── exact-duplicate check
                    └── local TXT/Markdown/PDF/DOCX understanding
                          └── versioned deterministic recommendation rules
                                └── version-bound approval review state
                                      └── guarded no-overwrite move
                                            └── append-only action events
                                                  ├── local data/library
                                                  ├── versioned FastAPI endpoints
                                                  └── React intake dashboard
```

## Boundaries

### Local API action guard

- Keeps read-only local API requests available without an account.
- Requires `X-Nova-Intent: local-user-action` on every request that changes
  Nova's state.
- Forces browser callers through the configured CORS origin check before a
  mutating request can be sent.
- Is a browser request-integrity boundary, not remote access or user
  authentication.
- Rejects unexpected Host values before a request reaches the API routes.

### Local dashboard HTTP boundary

- Serves the production dashboard only for `localhost` and `127.0.0.1`.
- Closes requests carrying an unexpected Host value.
- Uses a restrictive Content Security Policy and disables framing,
  content-type guessing, referrer leakage, and unused device permissions.
- Retains local HTTP because Docker publishes only to the loopback interface.

### Frontend

- Provides a separate local chat page with model selection, streamed replies,
  local conversation history, and stop generation.
- Shows editable knowledge proposals with explicit **Approve & save** and
  **Don't save** controls.
- Makes pending state explicit: a proposal is not permanent knowledge.
- States that tools, web access, RAG, and autonomous actions remain
  unavailable.
- Displays service health, intake totals, file metadata, duplicate status, and
  normalized understanding results.
- Reads authoritative, unfiltered totals from a dedicated summary endpoint so
  dashboard metrics do not change when search filters are active.
- Provides server-backed, relevance-ranked text search and metadata/status
  filters.
- Displays category, filename, destination, confidence, and explanation for
  deterministic recommendations.
- Provides approve, edit, reject, ignore, and review-again controls.
- Keeps approval and execution visibly separate.
- Requires confirmation for a move and presents guarded undo only when eligible.
- Displays the latest state of each append-only audited operation.
- Displays structured extraction diagnostics without exposing stack traces.
- Displays stored learning groups, active/reverted example totals, and the
  currently eligible destination candidate.
- Displays read-only database size, intake-drive headroom, latest scan timing,
  and conservative operational warnings without receiving host paths.
- Requires exact typed confirmation before forgetting a learning group.
- Can request an immediate scan.
- Does not receive file contents.
- Owns interaction state, not authoritative inventory data.

### Backend

- Discovers models and streams replies through a small Nova-owned Ollama
  adapter rather than coupling the application to a provider-specific UI.
- Stores conversations and complete user/assistant messages locally in SQLite.
- Detects only bounded, deterministic explicit-memory and high-value profile
  patterns; the language model does not decide what becomes permanent.
- Stores each proposal as pending and writes no permanent record before owner
  approval.
- Stores approved record contents in SQLite and writes a checksum-bound,
  no-overwrite Markdown copy under the configured knowledge directory.
- Keeps optional proposal failure isolated so ordinary chat remains available
  with a truthful warning.
- Stores no partial or invented assistant message when generation is stopped
  or the provider fails.
- Requires the local browser-intent guard for conversation creation, message
  submission, and proposal review.
- Scans the configured intake directory.
- Reads every file locally to calculate its fingerprint.
- Extracts UTF-8 text, PDF text layers, and DOCX document text up to the
  configured source and expanded-content limits.
- Isolates parser failures to an individual understanding record and continues
  background monitoring after a failed scan.
- Reconciles inventory records and duplicate ownership when source files are
  removed from the intake folder.
- Stores normalized metadata and understanding results in SQLite.
- Records the latest scan outcome and duration in process memory and reports
  safe storage and database measurements through a read-only status endpoint.
- Applies versioned deterministic invoice and project filing rules after local
  understanding completes.
- Persists either an explainable suggestion or an explicit
  `insufficient_evidence` outcome.
- Validates and stores review state against the exact recommendation generation
  that was reviewed.
- Treats missing or stale review state as awaiting review.
- Executes only a current approved recommendation for a non-duplicate file.
- Resolves source and destination beneath configured roots, refuses overwrite,
  and verifies SHA-256 before source removal.
- Records started, succeeded, and failed move or undo events append-only.
- Reverses a move only when the filed copy is unchanged and the original intake
  path is free.
- Indexes supported extracted text locally for case-insensitive search across
  filenames, paths, titles, content, evidence, extraction errors, and
  recommendation fields.
- Requires every unquoted search term to match somewhere in the record, treats
  quoted text as a phrase, and ranks exact filename, filename, and title matches
  above metadata, content, and evidence matches.
- Records a destination-learning example only after a successful approved move
  whose category was not corrected.
- Invalidates that example when the corresponding move is successfully undone.
- Applies a learned destination only to future suggestions after the configured
  minimum support and preference-share thresholds are met.
- Lists learning summaries without exposing source document text or filenames.
- Removes a learning group's derived examples transactionally only after exact
  confirmation, advances its revision, and records a reset event.
- Exposes versioned endpoints under `/api/v1`.
- Keeps the complete intake workflow available without an AI model or cloud
  service. The optional chat page requires the configured local Ollama service.

### Local storage

- Pending files remain in `data/intake`.
- Explicitly filed documents are stored under `data/library`.
- Chat conversations and messages live in the local SQLite database and are
  included in Nova's verified database backups.
- Docker mounts the local `data` root so the guarded action boundary can move
  approved files; scanning and recommendation paths do not write to files.
- SQLite lives in the `nova_data` Docker volume.
- Runtime data is excluded from Git.

### Windows operations

- Friendly root-level launchers delegate to one PowerShell controller.
- Start builds in detached mode, waits for the API and dashboard, and opens the
  loopback-only URL. Readiness uses explicit IPv4 loopback probes, allows up to
  three minutes for a slower first container start, and preserves the last
  probe failure for diagnostics.
- Stop uses ordinary Compose shutdown and never removes the named database
  volume.
- Status reports Compose state and the versioned health endpoint, compares the
  running version with the current checkout, and gives a direct rebuild action
  when they differ. The one-click status path also invokes a separate,
  on-demand SQLite quick check through a read-only database connection. A
  failed check returns safe recovery guidance without exposing local paths.
- Update refuses a dirty worktree and uses Git fast-forward-only before
  rebuilding, so it cannot silently replace local edits. When the current
  service is running, it creates and verifies an online database snapshot
  before downloading source changes; a backup failure stops the update.
- Backup creation reports full verification only after SQLite integrity and
  SHA-256 checks pass. Backup history reports filename-bound checksum
  availability separately and never presents an un-rechecked historical item
  as currently verified. Inventory assembly tolerates a backup disappearing
  between directory discovery and metadata capture, so one external local
  deletion does not suppress the remaining recovery points.
- Missing Docker, inactive Docker Desktop, missing Git, build failures, and
  startup timeouts produce direct recovery guidance.

## Intake record

Each observed file has:

- Permanent ID
- Relative path and original filename
- Extension and byte size
- Modified and observed timestamps
- SHA-256 fingerprint
- Status: `observed` or `duplicate`
- Canonical file reference when it is an exact duplicate

Supported text files also have a normalized understanding record:

- Extraction status
- Document type
- Derived title
- Short text preview
- Word and character counts
- Plain-language extraction evidence
- Error detail, stable error code, extraction method, and retry guidance when
  local extraction fails

The database stores searchable extracted text for supported files, alongside the
short preview returned by the API. Full extracted content never leaves the
backend through the intake listing endpoint.
PDF extraction uses pypdf; DOCX extraction reads the Open XML package locally.
Scanned PDFs without a text layer produce an empty result rather than invoking a
cloud OCR service.

Each file also receives a versioned recommendation record:

- Outcome: `suggested` or `insufficient_evidence`
- Suggested category, approved-format filename, and destination when available
- Confidence score
- Plain-language reasons
- Source fingerprint and intake status used to produce the result
- Rules version and generation timestamp

Recommendations are recalculated after content, understanding-result, or
duplicate-status changes and when the rules version changes. Exact duplicates
are never recommended for independent filing. These records are proposals only:
they cannot invoke execution.

A destination preference may modify a future proposal only when at least three
active successful moves share the same document type and unchanged base
category, and one destination accounts for at least 75% of those examples.
Ties and weaker evidence produce no preference. Each learning change advances a
per-group revision so cached recommendations are refreshed without disturbing
unrelated document groups. The explanation identifies the supporting example
count and reminds the user that approval remains required.

Users can inspect every stored learning group, including inactive examples
retained after undo. Forgetting a group deletes its derived examples, refreshes
affected recommendations, and records a local reset event with the group and
removed count. It does not alter source files, filed documents, approvals, or
the append-only file-action history.

Each suggested recommendation may also have one current approval record:

- Status: `pending`, `approved`, `rejected`, or `ignored`
- Reviewed category, filename, and destination
- Exact recommendation generation timestamp
- Review timestamp

An edit stores corrected fields with `pending` status. Approval without new
fields uses the latest edited values. When the recommendation generation
changes, its earlier review no longer joins to the current result and the file
returns to the review queue. This table stores current review state separately
from the append-only action audit.

Every execution or undo operation writes immutable action events:

- Stable operation and file IDs
- Kind: `move` or `undo`
- State: `started`, `succeeded`, or `failed`
- Relative source and destination paths
- Verified SHA-256 fingerprint
- Related move operation for undo
- Safe detail and timestamp

The latest event presents the operation's current state, while all preceding
events remain in SQLite. A `started` event is committed before touching the
filesystem so interrupted work remains visible rather than being guessed away.

## Security baseline

- Local-only deployment
- Non-root backend container
- Explicit CORS origins
- No secrets or runtime files in source control
- Tracked-file policy checks for common credential, private-key, database, and
  runtime-data filename patterns
- Human-readable container base-image tags paired with immutable verified
  image-index digests
- No automatic move, overwrite, permanent deletion, upload, or sharing
- Approval records intent only; execution requires a separate confirmed request
- Source and destination containment checks
- Exclusive destination creation
- Destination and source SHA-256 verification before source removal
- Guarded undo with path and fingerprint conflict checks
- Bounded source-file and expanded-text processing
- Parser errors are logged locally while safe diagnostics are returned to the UI
- AI providers disabled until explicitly configured

## Evolution rules

1. Build complete vertical slices.
2. Preserve original files as the source of truth.
3. Explain recommendations before requesting approval.
4. Make material actions reversible and auditable.
5. Keep AI optional for core operation.
6. Add infrastructure only from measured need.
