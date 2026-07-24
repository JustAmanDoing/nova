# Nova Architecture

## Purpose

Nova is a local-first personal assistant platform. The MVP proves one safe,
useful workflow before autonomy is introduced:

```text
Observe → Understand → Recommend → Approve → Execute → Audit → Learn
```

**Observe**, **Understand**, deterministic **Recommend**, explicit **Approve**,
guarded **Execute**, and append-only **Audit** are active today. Nova changes a
file only through a separate confirmed action that passes current-approval,
path, conflict, and fingerprint checks.

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

### Frontend

- Displays service health, intake totals, file metadata, duplicate status, and
  normalized understanding results.
- Reads authoritative, unfiltered totals from a dedicated summary endpoint so
  dashboard metrics do not change when search filters are active.
- Provides server-backed text search and metadata/status filters.
- Displays category, filename, destination, confidence, and explanation for
  deterministic recommendations.
- Provides approve, edit, reject, ignore, and review-again controls.
- Keeps approval and execution visibly separate.
- Requires confirmation for a move and presents guarded undo only when eligible.
- Displays the latest state of each append-only audited operation.
- Displays structured extraction diagnostics without exposing stack traces.
- Can request an immediate scan.
- Does not receive file contents.
- Owns interaction state, not authoritative inventory data.

### Backend

- Scans the configured intake directory.
- Reads every file locally to calculate its fingerprint.
- Extracts UTF-8 text, PDF text layers, and DOCX document text up to the
  configured source and expanded-content limits.
- Isolates parser failures to an individual understanding record and continues
  background monitoring after a failed scan.
- Reconciles inventory records and duplicate ownership when source files are
  removed from the intake folder.
- Stores normalized metadata and understanding results in SQLite.
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
- Exposes versioned endpoints under `/api/v1`.
- Runs without an AI model or cloud service.

### Local storage

- Pending files remain in `data/intake`.
- Explicitly filed documents are stored under `data/library`.
- Docker mounts the local `data` root so the guarded action boundary can move
  approved files; scanning and recommendation paths do not write to files.
- SQLite lives in the `nova_data` Docker volume.
- Runtime data is excluded from Git.

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
