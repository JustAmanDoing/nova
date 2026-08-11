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
        ├── approved-only knowledge retrieval
        │     ├── path containment + current SHA-256 verification
        │     └── exact persisted [K#] source evidence
        ├── exact Conductor capability routing
        │     ├── Focus next actions and verified projects/goals
        │     ├── read-only Librarian review
        │     └── read-only Project Record status
        └── Nova-owned provider adapter
              └── optional Ollama on the Windows host
```

It does not bypass or extend the guarded file workflow.

## Approved future interaction direction

The approved [NOVA Conductor interaction north star](conductor-interaction-north-star.md)
defines a future single conversational interface over NOVA's existing domain
services. It is a product direction, not a claim that agent delegation, voice
routing, background work, or proactive notification exists today.

The first Conductor slice must remain a small orchestration layer inside the
modular monolith. Existing services retain their authority, and every material
action retains its approval, audit, and recovery boundaries. Specialist agents
may be introduced only through a separately approved, measured capability.

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
- Remains unchanged when the owner uses the approved private phone route;
  Nginx supplies the already-allowed `localhost` Host value to the backend.

### Local and private dashboard HTTP boundary

- Serves the production dashboard for `localhost`, `127.0.0.1`, and at most
  one exact Tailscale DNS name recorded by the guarded Windows control.
- Closes requests carrying an unexpected Host value.
- Uses a restrictive Content Security Policy and disables framing,
  content-type guessing, referrer leakage, and unused device permissions.
- Retains local HTTP behind Docker's loopback-only publication.
- Uses Tailscale Serve to terminate HTTPS only for authenticated tailnet
  devices; Tailscale Funnel and router port forwarding are prohibited.
- Proxies `/api/` inside the existing frontend container so the phone uses one
  browser origin and backend CORS or Host trust does not expand.
- Keeps private phone access optional and explicitly reversible; desktop use
  does not depend on Tailscale.

### Frontend

- Provides a separate local chat page with model selection, streamed replies,
  local conversation history, and stop generation.
- Lists four exact local status requests that remain usable without Ollama and
  shows their source, check time, result hash, and owning NOVA page.
- Shows editable knowledge proposals with explicit **Approve & save** and
  **Don't save** controls.
- Makes pending state explicit: a proposal is not permanent knowledge.
- Shows exact approved source labels, titles, and local relative paths when
  knowledge is used.
- Shows a clear no-match message when no approved knowledge qualifies.
- Lists active and retired knowledge records and preserves immutable revision
  history.
- Requires exact typed confirmation before retiring a record and explains that
  retirement excludes it from future retrieval without deleting its files or
  history.
- Creates verified, checksum-recorded local knowledge snapshots on request.
- Reports priority-weighted core coverage, freshness, bounded retrieval
  self-checks, and highest-value knowledge gaps without scoring the owner.
- Lets the owner prepare an editable chat prompt for a missing or review-due
  area; preparation alone sends nothing and stores nothing.
- Shows static, catalogue-owned examples only for missing knowledge checks or
  an opened missing Librarian check. Choosing one prepares editable Chat text
  and never sends, approves, or saves it automatically.
- Provides a separate read-only-first Focus page that projects only active,
  owner-approved, checksum-verified `project` and `goal` records.
- Provides a separate read-only Project record page that catalogues current
  release state, exact repository-document snapshots, dated local archives,
  and explicitly supplied raw NOVA sources.
- Verifies every project-record source against its recorded size and SHA-256
  before offering a bounded escaped plain-text preview.
- Labels raw imported chat sources as unapproved evidence and never represents
  them as permanent knowledge or automatically supplies them to the model.
- Shows deterministic 90-day review state without inferring progress,
  priority, dates, deadlines, plans, tasks, or next actions.
- Routes additions and record reviews back through the existing chat proposal
  and immutable knowledge lifecycle rather than creating another write path.
- States that tools, web access, general document search, and autonomous
  actions remain unavailable.
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
- Publishes a static four-item Conductor registry and routes only its exact
  normalized phrases to existing read-only domain-service methods.
- Bounds Conductor lists to five items per section and persists capability ID,
  fixed local source, generation time, and result SHA-256 with the completed
  assistant message.
- Keeps ordinary chat and selected-document turns model-dependent; an
  unmatched model-free request fails before chat history is changed.
- Stores conversations and complete user/assistant messages locally in SQLite.
- Detects only bounded, deterministic explicit-memory and high-value profile
  patterns; the language model does not decide what becomes permanent.
- Stores each proposal as pending and writes no permanent record before owner
  approval.
- Stores approved record contents in SQLite and writes a checksum-bound,
  no-overwrite Markdown copy under the configured knowledge directory.
- Retrieves only records whose candidate is approved, whose resolved Markdown
  path remains beneath the knowledge root, and whose live file still matches
  the approved SHA-256.
- Uses bounded deterministic lexical scoring and supplies at most three
  approved records to one model turn.
- Persists a checksum-bound source snapshot with the assistant message so
  citations survive reloads and verified database backups.
- Records an explicit checked-with-no-match state rather than implying that
  unknown personal information was searched successfully.
- Keeps optional proposal failure isolated so ordinary chat remains available
  with a truthful warning.
- Stores no partial or invented assistant message when generation is stopped
  or the provider fails.
- Requires the local browser-intent guard for conversation creation, message
  submission, and proposal review.
- Rejects duplicate permanent knowledge unless the owner explicitly chooses to
  keep a separate record.
- Builds the Focus projection from the existing knowledge source of truth,
  verifies each current Markdown path and SHA-256, excludes verification
  failures with a safe aggregate warning, and marks verified records older than
  90 days as review due.
- Updates approved knowledge through immutable revisions with checksum-bound,
  no-overwrite Markdown files.
- Retires knowledge without deleting any approved revision or audit event and
  excludes retired records from future retrieval.
- Creates verified ZIP snapshots containing the manifest, current records,
  every immutable revision, and checksum-verified Markdown files.
- Calculates knowledge coverage only from verified active records against a
  published priority-weighted capability checklist.
- Calculates freshness from review windows and runs bounded retrieval
  self-checks that reapply path-containment and checksum verification.
- Produces deterministic missing-information and review-due suggestions; the
  language model does not score coverage or decide what information is
  required.
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
- Approved knowledge records live in SQLite and as checksum-bound Markdown
  copies under the configured knowledge directory.
- Every approved update creates a new no-overwrite Markdown revision while the
  previous revision and append-only record event remain available.
- Retired records and their files remain local and auditable but are excluded
  from new retrieval.
- Verified knowledge snapshots are written beneath the local backup root and
  never modify the live knowledge store.
- The Focus workspace introduces no second project store, task database, or
  generated planning data; it reads the existing verified knowledge records.
- Historical chat citations are stored in SQLite; every new retrieval verifies
  the current Markdown path and checksum before use.
- The project archive lives under the separately configured local archive root,
  mapped to `N:\Nova\Archive` on the Windows host and mounted read-only in the
  backend container.
- The project-record index is derived evidence. Git and release documentation,
  verified runtime state, approved knowledge, and original raw imports retain
  their existing authority.
- Exact release documentation snapshots and raw imports are no-overwrite and
  checksum-bound. Raw archive data is excluded from Git.
- Docker mounts the local `data` root so the guarded action boundary can move
  approved files; scanning and recommendation paths do not write to files.
- SQLite lives in the `nova_data` Docker volume.
- Runtime data is excluded from Git.

### Windows operations

- Friendly root-level launchers delegate to one PowerShell controller.
- Separate project-record launchers refresh the verified local catalogue or
  import one explicitly selected source. Imports require typed confirmation,
  reject likely full-account ChatGPT exports, preserve originals with no
  overwrite, and create no approved knowledge.
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
