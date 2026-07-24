# Nova Architecture

## Purpose

Nova is a local-first personal assistant platform. The MVP proves one safe,
useful workflow before autonomy is introduced:

```text
Observe → Understand → Recommend → Approve → Execute → Audit → Learn
```

**Observe**, **Understand**, and the first deterministic **Recommend** slice are
active today. Nova records files, extracts supported text locally, proposes
filing details when evidence is strong enough, and never changes source files.

## Current vertical slice

```text
Local data/intake folder (read-only mount)
  └── periodic or manual scan
        └── metadata + SHA-256 fingerprint
              └── exact-duplicate check
                    └── local TXT/Markdown/PDF/DOCX understanding
                          └── versioned deterministic recommendation rules
                                └── local SQLite inventory
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
- Indexes supported extracted text locally for case-insensitive search across
  filenames, paths, titles, content, evidence, extraction errors, and
  recommendation fields.
- Exposes versioned endpoints under `/api/v1`.
- Runs without an AI model or cloud service.

### Local storage

- Intake files remain in `data/intake`.
- Docker mounts the intake folder read-only.
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
there is no approval or execution path in the current milestone.

## Security baseline

- Local-only deployment
- Read-only intake mount
- Non-root backend container
- Explicit CORS origins
- No secrets or runtime files in source control
- No automatic rename, move, delete, upload, or sharing
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
