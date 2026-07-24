# Nova Architecture

## Purpose

Nova is a local-first personal assistant platform. The MVP proves one safe,
useful workflow before autonomy is introduced:

```text
Observe → Understand → Recommend → Approve → Execute → Audit → Learn
```

Only **Observe** is active today. Nova records files without changing them.

## Current vertical slice

```text
Local data/intake folder (read-only mount)
  └── periodic or manual scan
        └── metadata + SHA-256 fingerprint
              └── exact-duplicate check
                    └── local SQLite inventory
                          ├── versioned FastAPI endpoints
                          └── React intake dashboard
```

## Boundaries

### Frontend

- Displays service health, intake totals, file metadata, and duplicate status.
- Can request an immediate scan.
- Does not receive file contents.
- Owns interaction state, not authoritative inventory data.

### Backend

- Scans the configured intake directory.
- Reads files only to calculate their fingerprint.
- Stores normalized metadata in SQLite.
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

No classification or content extraction is performed yet.

## Security baseline

- Local-only deployment
- Read-only intake mount
- Non-root backend container
- Explicit CORS origins
- No secrets or runtime files in source control
- No automatic rename, move, delete, upload, or sharing
- AI providers disabled until explicitly configured

## Evolution rules

1. Build complete vertical slices.
2. Preserve original files as the source of truth.
3. Explain recommendations before requesting approval.
4. Make material actions reversible and auditable.
5. Keep AI optional for core operation.
6. Add infrastructure only from measured need.
