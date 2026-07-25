# Nova

[![Continuous verification](https://github.com/JustAmanDoing/nova/actions/workflows/ci.yml/badge.svg)](https://github.com/JustAmanDoing/nova/actions/workflows/ci.yml)

Nova is a local-first personal AI foundation that begins with safe, explainable
file intake. Its core remains useful without an AI provider.

The current MVP can:

- Observe files placed in a local intake folder
- Record filename, path, size, timestamps, and SHA-256 fingerprint
- Detect exact duplicates without deleting either copy
- Extract TXT, Markdown, PDF, and DOCX content locally
- Extract text from PNG, JPEG, TIFF, and BMP images with bounded local OCR
- Fall back to local OCR when a PDF has no readable text layer
- Record a title, short preview, word count, and extraction evidence
- Mark empty, oversized, failed, and not-yet-supported files clearly
- Store the inventory in local SQLite
- Display intake status in a responsive local dashboard
- Search filenames, paths, extracted text, titles, evidence, and extraction
  errors with deterministic relevance ranking
- Filter by intake status, understanding status, extension, and document type
- Show structured extraction diagnostics with method, error code, and retry guidance
- Apply deterministic invoice and project rules before any AI is considered
- Suggest a category, approved-format filename, and destination with confidence
- Explain why each suggestion was made, or return no recommendation when evidence is weak
- Review suggestions by approving, editing, rejecting, or ignoring them
- Filter files by current review status
- Return changed recommendations to the review queue automatically
- Move a currently approved file into the local library only after a separate
  confirmation
- Refuse changed sources, occupied destinations, duplicates, and stale approvals
- Record every started, successful, or failed operation in an append-only audit
- Undo a completed move when the filed copy and original path remain safe
- Detect operations left incomplete after an interruption and diagnose the
  current source, destination, and SHA-256 state without changing either file
- Create consistent, integrity-checked SQLite backups with SHA-256 checksums
  while Nova remains running
- Restore only a verified database backup after exact typed confirmation,
  automatically preserving the current database as a safety snapshot
- Apply ordered, recorded SQLite schema migrations without discarding existing
  intake, recommendation, review, or audit data
- Refuse an unreadable or corrupt active database before applying migrations
- Learn a preferred destination only after at least three consistent,
  successful approved moves, while preserving explicit approval and execution
- Show every stored preference group and forget its derived examples only
  after exact typed confirmation, without changing files or action history
- Recover background monitoring after an individual scan or parser failure
- Reconcile removed files and duplicate ownership with the current intake folder
- Keep dashboard totals accurate while search filters are active
- Run automatic background scans or a manual scan
- Reject browser-triggered state changes that do not come through Nova's
  permitted local interface
- Reject unexpected local HTTP Host values and serve restrictive browser
  security headers
- Prevent browsers and intermediaries from caching Nova API responses
- Revalidate the dashboard entry page after updates to avoid stale asset links
- Use patched test-tool versions with a vulnerability-reviewed dependency lock
- Pin external CI actions to verified immutable commits
- Verify guarded move, undo, backup, and restore against the production stack
- Preserve Linux container entrypoints across Windows Git checkouts
- Report database size, local storage headroom, and latest scan health without
  exposing paths or document content

Nova never moves a file automatically and never overwrites an existing file.
It does not upload, share, or permanently delete documents.

## Quick start with Docker

Prerequisite: Docker Desktop with Docker Compose.

### Windows

With Docker Desktop running, double-click **Start Nova.cmd** in the project
folder. Nova builds in the background, waits for both services to become
healthy, and opens the local dashboard.

- **Check Nova.cmd** shows container and health status, and warns when the
  running application does not match the version in the current project
  folder.
- **Stop Nova.cmd** stops the containers without deleting the database or
  document folders.
- **Update Nova.cmd** refuses local changes, downloads only a fast-forward Git
  update, rebuilds Nova, and opens it. When Nova is already running, it first
  creates and verifies a local database backup; a failed backup stops the update
  before source changes are downloaded.

Each launcher uses the shared, reviewable `scripts/Nova.ps1` controller. It
does not install software, delete Docker volumes, or expose Nova beyond this
PC. If a build fails or Nova does not become ready, the controller prints the
container state, the most recent 80 log lines, and the last readiness error so
the cause is visible without searching through Docker Desktop. Readiness probes
use the exact IPv4 loopback addresses exposed by Compose and allow slower
first-time Windows container starts up to three minutes.

### Command line

```bash
docker compose up --build
```

Open:

- Nova: http://localhost:5173
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/api/v1/health

Place a TXT, Markdown, PDF, DOCX, PNG, JPEG, TIFF, or BMP test file in
`data/intake`. Nova scans automatically every three seconds, or you can select
**Scan now** in the dashboard. The local `data` root is mounted into the
backend; scans remain read-only, while an explicitly confirmed move can place
an approved file under `data/library`.

Nova extracts and locally indexes UTF-8 text, PDF text layers, DOCX document
text, and supported images. A PDF with no readable text layer is rendered to
bounded page images and processed by local Tesseract OCR. The Docker image
includes Tesseract English data and Poppler; no document or OCR content is sent
to a remote service. Search is case-insensitive and runs against the local
SQLite inventory; file contents are never returned by the API. Multiple
unquoted terms must all match, quoted text is treated as one phrase, and exact
filename, filename, and title matches rank above metadata, content, and
evidence matches.

Recommendations are local, deterministic, and read-only. The first rules cover
invoice and project documents. Nova stores a versioned result, exposes its
plain-language reasons in the dashboard, and deliberately returns **No
recommendation** when evidence is insufficient. A recommendation alone never
renames or moves a source file.

Approval records intent against one exact recommendation version. Execution is
a separate confirmed action. Before moving, Nova revalidates the approval,
source location, destination, and SHA-256 fingerprint. It copies without
overwrite, verifies both copies, then removes the source. Undo applies the same
checks in reverse. Operation events remain in the local append-only audit.

Nova can adjust a future destination suggestion after at least three successful
approved moves with the same document type and unchanged category, and only
when one destination represents at least 75% of active examples. An undo
invalidates its example immediately. Learning changes the destination proposal
only; approval and the separately confirmed move remain mandatory. The
dashboard shows active and reverted example totals by group. **Forget
examples** permanently removes that derived learning only after exact typed
confirmation and records a local reset event.

If an operation remains in `started` state for five minutes, Nova inspects both
recorded paths without changing them. The dashboard explains whether the source
is safe to retry, the destination indicates likely completion, two verified
copies remain, or the current state needs manual attention. Nova never performs
automatic recovery from an ambiguous or interrupted operation.

The **Create backup** action uses SQLite's online backup API to produce a
consistent snapshot under `data/backups`. Every successful backup passes
SQLite's integrity check and receives a SHA-256 checksum sidecar. Nova never
overwrites or automatically deletes an earlier backup. The dashboard lists the
five newest snapshots and provides a download link.

The **Restore** action is available only for a backup with a valid checksum
sidecar. The API verifies the SHA-256 value and SQLite integrity, creates a new
verified safety snapshot of the current database, and then replaces the
database under the same lock used by scans and file actions. Nova validates and
reconciles the restored database before reporting success. If validation fails,
it restores the safety snapshot automatically. Each attempt that changes the
database is recorded in `data/backups/restore-audit.jsonl`.

Restore changes Nova's local database state, including extracted text,
recommendations, reviews, and action history. It does not restore, move, remove,
or overwrite document files. After restoration, Nova reconciles the derived
intake inventory with the files that are currently on disk. The dashboard
requires typing `RESTORE <backup filename>` exactly before it sends the request.

Nova records every database schema step in `schema_migrations`. Startup applies
only missing migrations, one ordered step at a time, and each step uses a
transactional savepoint. Existing pre-migration databases are adopted
idempotently without deleting records. Nova refuses to open a database created
by a newer unsupported version or one whose recorded migration names do not
match the running build. The earlier `schema_meta` version remains updated for
compatibility.

Two independent limits protect local resources:

- `NOVA_MAX_TEXT_BYTES` limits the source file size accepted for extraction.
- `NOVA_MAX_EXTRACTED_TEXT_BYTES` limits expanded text from parsers such as PDF
  and DOCX, including compressed document content.
- `NOVA_ACTION_STALE_SECONDS` controls how long a started operation may remain
  active before Nova reports it for read-only recovery assessment.
- `NOVA_OCR_MAX_PAGES` limits scanned-PDF OCR page count.
- `NOVA_OCR_TIMEOUT_SECONDS` bounds one complete local OCR operation.
- `NOVA_OCR_MAX_RENDER_DIMENSION` bounds the longest rendered PDF-page edge.
- `NOVA_OCR_MAX_RENDERED_BYTES` bounds temporary rendered page storage.
- `NOVA_OCR_ENABLED=false` disables image and scanned-PDF OCR.
- `NOVA_ALLOWED_HOSTS` lists the Host values accepted by the local API.

Stop Nova with:

```bash
docker compose down
```

The SQLite inventory and action audit remain in a Docker volume between
restarts. Filed documents remain on disk under `data/library`. Use
`docker compose down -v` only when you intentionally want to erase Nova's local
inventory and audit; it does not remove filed documents.

Docker publishes Nova only on `127.0.0.1`, so the dashboard and API are
available from this PC but not other devices on the network. Backups may contain
extracted document text and audit history; keep `data/backups` private.

The local interface also adds `X-Nova-Intent: local-user-action` to every
state-changing API request. This forces browser callers to pass Nova's CORS
preflight before they can request a scan, review, file action, backup, restore,
or learning reset. The header is a local browser-integrity boundary rather than
an account or remote-access system.

Both local services accept only `localhost` and `127.0.0.1` Host values by
default. The dashboard also blocks framing, external scripts, content-type
guessing, referrer leakage, and unused camera, microphone, and location access.
`NOVA_ALLOWED_HOSTS` can add an explicitly approved backend host without
changing Docker's loopback-only port binding.

The **System health** panel reports the database size, free space on the drive
containing `data/intake`, and latest scan duration and outcome. It warns below
5 GB or 10% free space, after a failed scan, or when a scan exceeds 30 seconds.
These warnings are advisory: Nova never deletes, archives, uploads, or moves
data in response.

## Local development

### Backend

Requires Python 3.12+.

Direct local OCR also requires `tesseract` and `pdftoppm` on the system path.
The Docker image installs both automatically.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --constraint constraints.txt -e ".[dev]"
uvicorn app.main:app --reload
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run checks:

```bash
pytest
ruff check .
mypy app
```

### Frontend

Requires Node.js 20+ and pnpm 9.15.5.

```bash
cd frontend
corepack enable
corepack prepare pnpm@9.15.5 --activate
pnpm install --frozen-lockfile
pnpm run dev
```

Run checks:

```bash
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run build
```

GitHub Actions repeats the backend, frontend, Windows-launcher, Compose, and
production-container checks for every pull request and update to `main`. It
also launches an isolated production stack and verifies the API, dashboard,
and indexing of one synthetic file. The workflow never deploys Nova or accesses
user document data.

The backend container initializes only Nova's mounted intake, library, backup,
and database directories before immediately dropping to its unprivileged
`nova` account. This keeps the same Compose setup portable across Windows,
Linux, and hosted verification runners without running the application as root.
Continuous verification checks this property against the live container.

Nova also rejects overlapping intake, library, backup, and database paths
before scanning begins. Keep these locations as separate sibling paths.

The frontend container also pins Node 20 and pnpm 9.15.5. Update both
`frontend/package.json` and `frontend/Dockerfile` together when changing pnpm.

## Repository layout

```text
nova/
├── backend/            FastAPI, SQLite intake service, and tests
├── frontend/           React/Vite intake dashboard
├── docs/               Architecture and roadmap
├── data/intake/        Local intake folder; contents are ignored by Git
├── data/library/       Approved filed documents; contents are ignored by Git
├── .env.example        Safe local configuration template
└── docker-compose.yml  Local full-stack environment
```

## Safety

Never commit secrets, API keys, private documents, personal data, or a populated
`.env` file. Everything under `data/` is ignored by Git.

## Documentation

- [Architecture](docs/architecture.md)
- [Architecture review — 25 July 2026](docs/architecture-review-2026-07-25.md)
- [Milestone 3 recommendations](docs/milestone-3-recommendations.md)
- [Milestone 4 approval boundary](docs/milestone-4-approval.md)
- [Milestone 5 execution and undo](docs/milestone-5-execution.md)
- [Milestone 6 recovery diagnostics](docs/milestone-6-recovery.md)
- [Milestone 7 verified backups](docs/milestone-7-backups.md)
- [Milestone 8 guarded restore](docs/milestone-8-restore.md)
- [Milestone 9 ordered database migrations](docs/milestone-9-database-migrations.md)
- [Milestone 10 bounded local OCR](docs/milestone-10-local-ocr.md)
- [Milestone 11 confirmed preference learning](docs/milestone-11-confirmed-learning.md)
- [Milestone 12 ranked local search](docs/milestone-12-ranked-search.md)
- [Milestone 13 learning controls](docs/milestone-13-learning-controls.md)
- [Milestone 14 Windows controls](docs/milestone-14-windows-controls.md)
- [Milestone 15 continuous verification](docs/milestone-15-continuous-verification.md)
- [Milestone 16 local action guard](docs/milestone-16-local-action-guard.md)
- [Milestone 17 operational health](docs/milestone-17-operational-health.md)
- [Milestone 18 production runtime smoke test](docs/milestone-18-runtime-smoke-test.md)
- [Milestone 19 local HTTP hardening](docs/milestone-19-local-http-hardening.md)
- [Milestone 20 container storage portability](docs/milestone-20-container-storage-portability.md)
- [Milestone 21 validated storage boundaries](docs/milestone-21-storage-boundaries.md)
- [Milestone 22 bounded dashboard refresh](docs/milestone-22-bounded-dashboard-refresh.md)
- [Milestone 23 current ASGI test transport](docs/milestone-23-current-test-transport.md)
- [Milestone 24 reproducible Python dependencies](docs/milestone-24-python-dependency-constraints.md)
- [Milestone 25 automatic startup diagnostics](docs/milestone-25-startup-diagnostics.md)
- [Milestone 26 active database integrity guard](docs/milestone-26-database-integrity-guard.md)
- [Milestone 27 private API cache policy](docs/milestone-27-private-api-cache-policy.md)
- [Milestone 28 fresh dashboard entry page](docs/milestone-28-dashboard-cache-policy.md)
- [Milestone 29 dependency advisory remediation](docs/milestone-29-dependency-advisories.md)
- [Milestone 30 immutable CI actions](docs/milestone-30-immutable-ci-actions.md)
- [Milestone 31 full runtime workflow](docs/milestone-31-full-runtime-workflow.md)
- [Milestone 32 Windows-safe container checkout](docs/milestone-32-container-line-endings.md)
- [Milestone 33 runtime version guard](docs/milestone-33-runtime-version-guard.md)
- [Milestone 34 pre-update backup](docs/milestone-34-pre-update-backup.md)
- [Milestone 35 resilient Windows readiness](docs/milestone-35-windows-readiness.md)
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)
