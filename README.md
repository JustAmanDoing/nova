# Nova

[![Continuous verification](https://github.com/JustAmanDoing/nova/actions/workflows/ci.yml/badge.svg)](https://github.com/JustAmanDoing/nova/actions/workflows/ci.yml)

Nova is a local-first personal AI foundation that begins with safe, explainable
file intake. Its core remains useful without an AI provider.

The current MVP can:

- Discover local Ollama models and stream conversational replies
- Keep conversation and message history in Nova's local SQLite database
- Stop an in-progress reply without storing an invented or partial assistant answer
- Report local-model failure clearly while keeping saved conversations available
- Warn when proposed knowledge appears to duplicate an active approved record
- Require explicit confirmation before keeping likely duplicate records separately
- Update approved knowledge by creating a new immutable Markdown revision
- Retire approved knowledge from future retrieval without deleting its files
- Create checksum-verified knowledge snapshots containing every tracked revision
- Review read-only Librarian health across coverage, freshness, retrieval,
  integrity, and deterministic consistency
- Inspect duplicate, conflict, stale, missing, broken-reference, and checksum
  evidence without automatically changing knowledge
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
- Pin each container base-image tag to a verified immutable image-index digest
- Verify guarded move, undo, backup, and restore against the production stack
- Preserve Linux container entrypoints across Windows Git checkouts
- Report database size, local storage headroom, and latest scan health without
  exposing paths or document content
- Recheck the active database with SQLite's read-only quick check from the
  one-click Windows status control
- Use NOVA from the owner's authenticated Tailscale phone through a private
  same-origin HTTPS gateway without publishing either Docker service

Nova never moves a file automatically and never overwrites an existing file.
It does not upload, share, or permanently delete documents.

## Quick start with Docker

Prerequisite: Docker Desktop with Docker Compose.

### Windows

With Docker Desktop running, double-click **Start Nova.cmd** in the project
folder. Nova builds in the background, waits for both services to become
healthy, and opens the local dashboard.

- **Check Nova.cmd** shows container, application, and local-storage status.
  It reports Nova's safe operational warnings, runs an on-demand read-only
  database integrity check, and warns when the running application does not
  match the version in the current project folder.
- **Stop Nova.cmd** stops the containers without deleting the database or
  document folders.
- **Update Nova.cmd** refuses local changes, downloads only a fast-forward Git
  update, rebuilds Nova, and opens it. When Nova is already running, it first
  creates and verifies a local database backup; a failed backup stops the update
  before source changes are downloaded.
- **Phone Access On.cmd** records this PC's exact private Tailscale DNS name,
  applies the same-origin gateway, and enables Tailscale Serve only after
  refusing any existing unowned Serve configuration or public Funnel.
- **Check Phone Access.cmd** reports the private address, Funnel state, saved
  configuration ownership, and HTTPS health without changing anything.
- **Phone Access Off.cmd** removes phone access only when the live Serve
  configuration still matches the one NOVA recorded. Desktop access remains
  unchanged.
- **Update NOVA Project Record.cmd** verifies the installed release against
  its Git tag and `origin/main`, snapshots the exact release documentation,
  and atomically refreshes the checksum-bound catalogue under
  `N:\Nova\Archive`.
- **Import NOVA Source.cmd** preserves one explicitly selected NOVA-only chat
  or project source under `N:\Nova\Archive`. It requires typed confirmation,
  refuses overwrite and duplicate content, rejects likely full-account
  ChatGPT exports, and does not add the source to approved knowledge.

Each launcher uses the shared, reviewable `scripts/Nova.ps1` controller. It
does not install software or delete Docker volumes. The standard launchers
keep NOVA on this PC. The separately approved phone-access launcher can publish
the loopback frontend only to authenticated devices on the owner's Tailscale
network; it never enables public Funnel access or opens a router port. If a
build fails or Nova does not become ready, the controller prints the container
state, the most recent 80 log lines, and the last readiness error so the cause
is visible without searching through Docker Desktop. Readiness probes use the
exact IPv4 loopback addresses exposed by Compose and allow slower first-time
Windows container starts up to three minutes.

### Command line

```bash
docker compose up --build
```

Open:

- Nova: http://localhost:5173
- Local chat: http://localhost:5173/chat.html
- Projects and goals: http://localhost:5173/focus.html
- Local project record: http://localhost:5173/archive.html
- Librarian: http://localhost:5173/librarian.html
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/api/v1/health

### Local chat, approved knowledge capture, and retrieval

The **Chat** page uses the Ollama service already installed on the Windows host.
Model discovery and replies remain local. Conversation history is stored in
Nova's SQLite database and is therefore included in verified database backups.

Milestone 55 adds bounded, deterministic conversation-to-knowledge capture.
An explicit **Remember that...** request, or a limited high-value profile
statement such as a preference or goal, can prepare an editable review card.
The proposal remains pending until the owner selects **Approve & save**.
Selecting **Don't save** records the rejection and creates no permanent
knowledge file. Approved records are retained in SQLite and written as
no-overwrite Markdown records under the configured local knowledge directory.
The Windows deployment maps that directory to `N:\Nova\Memory`.

Milestone 56 retrieves only owner-approved records. Nova verifies that each
local Markdown copy remains inside the configured knowledge directory and still
matches its approved SHA-256 before supplying it to the model. Answers show
exact `[K#]` source cards, and citation evidence is stored with the assistant
message. If nothing approved matches, the chat says so clearly.

Milestone 57 adds owner-controlled lifecycle management. Likely duplicates are
flagged before approval and cannot be kept separately without explicit
confirmation. An approved record can be updated only by creating a new,
no-overwrite Markdown revision; its previous revisions remain unchanged.
Retirement removes a record from future retrieval without deleting any
revision. The owner can also create a checksum-verified ZIP snapshot containing
the lifecycle manifest and every tracked Markdown revision.

Milestone 58 adds a read-only **Knowledge health** report. It verifies every
active record before measuring priority-weighted core coverage, review-age
freshness, and deterministic retrieval quality. Its seven core areas and
matching rules are published in source. Optional opportunities never lower
core coverage. The report scores NOVA's knowledge capability, not the owner,
and it never saves, edits, retires, or uploads knowledge.

Milestone 59 makes those suggestions actionable without adding another
knowledge-writing path. **Add through chat** prepares a focused, editable
starter in the composer but never sends or saves it. A review-due suggestion
opens the exact approved record in the existing immutable lifecycle editor.
Permanent knowledge still requires the owner to send the completed prompt and
separately choose **Approve & save**.

Milestone 63 adds explicit, single-document context. The owner may select one
currently indexed, ready intake document for one chat turn. The backend
revalidates its intake boundary and SHA-256 before supplying at most 8,000
UTF-8 bytes as untrusted `[D1]` reference data. Completed replies retain only
source metadata for display; document text is not returned by selector or
citation APIs. NOVA does not select documents automatically.

Milestone 65 adds a separate read-only-first **Focus** page. It shows only
active owner-approved `project` and `goal` knowledge whose local Markdown file
still matches its recorded SHA-256. Projects and goals remain separate, and
each card shows its revision, last update, and deterministic 90-day review
state. An unverifiable record is excluded with a safe warning rather than
displayed from stale database content.

Empty sections link to the existing guided chat flow, which prepares an
editable prompt without sending or saving it. Record review links open the
existing immutable update and guarded retirement controls. The Focus page does
not infer progress, priority, dates, deadlines, plans, tasks, or next actions,
and it remains useful when Ollama is unavailable.

Milestone 68 adds a bounded **Next actions** section to Focus. Actions are
created only from text the owner explicitly submits in the local form. The
first lifecycle supports only open, complete, and reopen, while retaining an
append-only local event history. An action may be linked to one currently
verified active project; if that project later becomes retired or fails its
integrity check, NOVA hides the stale project content and reports the
association as unavailable.

Next actions are stored separately from permanent knowledge and do not alter
approved Markdown records. NOVA does not generate actions from chat,
documents, projects, or model output, and this slice adds no priorities,
dates, deadlines, reminders, recurrence, notifications, scheduling, or
autonomous execution. The view and lifecycle remain useful without Ollama.

Milestone 69 adds private phone access through the owner's existing Tailscale
network. The production frontend uses one browser origin and proxies `/api/`
to the unchanged backend service inside Docker. Both Windows-published ports
remain bound to loopback, the backend trust and CORS rules do not expand, and
the frontend accepts only localhost plus the exact private Tailscale DNS name
recorded by the guarded Windows control. Tailscale Funnel and router port
forwarding are explicitly excluded.

Milestone 76 adds the read-only **Project record** page. It catalogues one
canonical current-status record, exact release documentation snapshots, dated
local project records, existing development archives, and explicitly supplied
NOVA-only chat sources. Every source is checked against its recorded SHA-256
before NOVA offers a bounded plain-text preview.

Raw imported chat sources are evidence only. They remain outside Git and
separate from owner-approved knowledge, are not automatically supplied to the
model, and cannot be edited or deleted through the web interface. NOVA does
not access the owner's ChatGPT account, browser history, clipboard, or
unrelated conversations. ChatGPT information becomes local only when the
owner explicitly supplies one NOVA-only source through the guarded Windows
control.

Chat still cannot browse the web, use tools, perform semantic or general
document search, or take autonomous actions. Starting a conversation,
sending a message, and reviewing a knowledge proposal require the same local
browser-intent guard as other state-changing Nova requests. Stopping generation
preserves only records that the backend had already committed; it never
fabricates a completed assistant response.

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
overwrites or automatically deletes an earlier backup. The dashboard shows the
five newest snapshots first and provides a **Show all** control when additional
recovery points exist. It also summarizes the total retained backup count,
storage use, and whether each backup has a recorded checksum without deleting
anything. The history does not claim that an unchanged backup has been fully
reverified during listing. The API therefore reports checksum availability
separately from current verification: a newly created backup is verified before
publication, while a history entry reports only whether its filename-bound
checksum is recorded. A download link appears only when that complete checksum
record is available. Every download then rechecks both the SHA-256 checksum and
SQLite
integrity before returning the database or checksum sidecar. Keep both
downloaded files together on a different trusted drive; backups can contain
sensitive extracted text.

The foreground intake dashboard remains current on its bounded five-second
cycle. Backup history changes less frequently, so Nova refreshes that directory
inventory once per minute automatically and immediately after manual actions.
This avoids repeatedly reading every retained checksum sidecar as the recovery
history grows. If a backup is removed by another local process while that
inventory is being read, Nova keeps the remaining recovery points available
instead of failing the entire history request. A failed backup-history refresh
is retried on the next five-second dashboard cycle instead of being treated as
a successful minute-bounded refresh. Every dashboard data source settles
independently, so a failure in one panel does not prevent successful file,
summary, review, recovery, backup, learning, or operational updates from
appearing. Nova
preserves the last known data for the failed source, labels the affected area
in a scoped diagnostic, and retries it. A failed file-list request is kept
distinct from a genuinely empty intake.
If a slow earlier request finishes after a newer manual or automatic refresh,
Nova discards the older result instead of rolling the dashboard back to stale
state.

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
containing `data/intake`, and latest scan duration and outcome. It advises
capacity planning below both 25 GB and 20% free space, and reports more urgent
low-storage attention below 5 GB or 10%. It also reports a failed scan or one
that exceeds 30 seconds. These warnings are advisory: Nova never deletes,
archives, uploads, or moves data in response.

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
`.env` file. Everything under `data/` is ignored by Git. Common credential,
private-key, and local-database filename patterns are also ignored and checked
against the tracked file list during verification. See [Security policy](SECURITY.md)
for private vulnerability reporting and the local security boundary.

## Documentation

- [Architecture](docs/architecture.md)
- [Architecture review — 25 July 2026](docs/architecture-review-2026-07-25.md)
- [Intake MVP completion review — 25 July 2026](docs/intake-mvp-completion-review-2026-07-25.md)
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
- [Milestone 36 public repository hygiene](docs/milestone-36-repository-hygiene.md)
- [Milestone 37 immutable container bases](docs/milestone-37-immutable-container-bases.md)
- [Milestone 38 representative runtime acceptance](docs/milestone-38-representative-runtime-acceptance.md)
- [Milestone 39 storage capacity planning](docs/milestone-39-capacity-planning.md)
- [Milestone 40 verified backup export](docs/milestone-40-verified-backup-export.md)
- [Milestone 41 backup history visibility](docs/milestone-41-backup-history-visibility.md)
- [Milestone 42 backup capacity visibility](docs/milestone-42-backup-capacity-visibility.md)
- [Milestone 43 bounded backup refresh](docs/milestone-43-bounded-backup-refresh.md)
- [Milestone 44 latest dashboard state](docs/milestone-44-latest-dashboard-state.md)
- [Milestone 45 precise backup integrity status](docs/milestone-45-precise-backup-integrity-status.md)
- [Milestone 46 prompt backup refresh retry](docs/milestone-46-backup-refresh-retry.md)
- [Milestone 47 isolated backup refresh failure](docs/milestone-47-backup-refresh-isolation.md)
- [Milestone 48 independent dashboard resources](docs/milestone-48-independent-dashboard-resources.md)
- [Milestone 49 filename-bound backup checksums](docs/milestone-49-filename-bound-checksums.md)
- [Milestone 50 precise backup API states](docs/milestone-50-precise-backup-api-states.md)
- [Milestone 51 resilient backup inventory](docs/milestone-51-resilient-backup-inventory.md)
- [Milestone 52 on-demand database integrity](docs/milestone-52-on-demand-database-integrity.md)
- [Milestone 53 local v1 completion review](docs/milestone-53-local-v1-completion-review.md)
- [Milestone 54 local chat core](docs/milestone-54-local-chat-core.md)
- [Milestone 55 conversation-to-knowledge capture](docs/milestone-55-conversation-to-knowledge-capture.md)
- [Milestone 56 approved knowledge retrieval](docs/milestone-56-approved-knowledge-retrieval.md)
- [Milestone 57 knowledge lifecycle and duplicate controls](docs/milestone-57-knowledge-lifecycle.md)
- [Milestone 57 architecture review](docs/milestone-57-architecture-review.md)
- [Milestone 57 engineering review](docs/milestone-57-engineering-review.md)
- [Milestone 58 knowledge quality and gap analysis](docs/milestone-58-knowledge-quality-gap-analysis.md)
- [Milestone 58 architecture review](docs/milestone-58-architecture-review.md)
- [Milestone 58 engineering review](docs/milestone-58-engineering-review.md)
- [Milestone 59 guided knowledge onboarding proposal](docs/milestone-59-guided-knowledge-onboarding-proposal.md)
- [Milestone 59 guided knowledge onboarding](docs/milestone-59-guided-knowledge-onboarding.md)
- [Milestone 59 architecture review](docs/milestone-59-architecture-review.md)
- [Milestone 59 engineering review](docs/milestone-59-engineering-review.md)
- [Milestone 60 repository integration proposal](docs/milestone-60-repository-integration-proposal.md)
- [Milestone 60 architecture review](docs/milestone-60-architecture-review.md)
- [Milestone 60 engineering review](docs/milestone-60-engineering-review.md)
- [Milestone 60 final release report](docs/milestone-60-release-report.md)
- [Milestone 61 daily-use beta validation](docs/milestone-61-daily-use-beta-validation.md)
- [Milestone 61 architecture review](docs/milestone-61-architecture-review.md)
- [Milestone 61 engineering review](docs/milestone-61-engineering-review.md)
- [Milestone 62 next-capability selection](docs/milestone-62-next-capability-selection.md)
- [Milestone 62 architecture review](docs/milestone-62-architecture-review.md)
- [Milestone 62 engineering review](docs/milestone-62-engineering-review.md)
- [Milestone 63 explicit document context proposal](docs/milestone-63-explicit-document-context-proposal.md)
- [Milestone 63 architecture review](docs/milestone-63-architecture-review.md)
- [Milestone 63 engineering review](docs/milestone-63-engineering-review.md)
- [Milestone 63 release report](docs/milestone-63-release-report.md)
- [Milestone 64 next-capability selection](docs/milestone-64-next-capability-selection.md)
- [Milestone 64 architecture review](docs/milestone-64-architecture-review.md)
- [Milestone 64 engineering review](docs/milestone-64-engineering-review.md)
- [Milestone 65 active projects and goals workspace proposal](docs/milestone-65-active-projects-goals-workspace-proposal.md)
- [Milestone 65 implementation record](docs/milestone-65-implementation.md)
- [Milestone 65 architecture review](docs/milestone-65-architecture-review.md)
- [Milestone 65 engineering review](docs/milestone-65-engineering-review.md)
- [Milestone 65 Windows acceptance](docs/milestone-65-acceptance.md)
- [Milestone 65 release report](docs/milestone-65-release-report.md)
- [Milestone 66 Focus workspace daily-use validation](docs/milestone-66-focus-workspace-daily-use-validation.md)
- [Milestone 66 architecture review](docs/milestone-66-architecture-review.md)
- [Milestone 66 engineering review](docs/milestone-66-engineering-review.md)
- [Milestone 67 next-capability selection](docs/milestone-67-next-capability-selection.md)
- [Milestone 67 architecture review](docs/milestone-67-architecture-review.md)
- [Milestone 67 engineering review](docs/milestone-67-engineering-review.md)
- [Milestone 68 owner-approved next actions proposal](docs/milestone-68-owner-approved-next-actions-proposal.md)
- [Milestone 68 implementation record](docs/milestone-68-implementation.md)
- [Milestone 68 architecture review](docs/milestone-68-architecture-review.md)
- [Milestone 68 engineering review](docs/milestone-68-engineering-review.md)
- [Milestone 68 Windows acceptance](docs/milestone-68-acceptance.md)
- [Milestone 68 release report](docs/milestone-68-release-report.md)
- [Milestone 69 secure phone access proposal](docs/milestone-69-secure-phone-access-proposal.md)
- [Milestone 70 phone daily-use validation](docs/milestone-70-phone-daily-use-validation.md)
- [Milestone 70 architecture review](docs/milestone-70-architecture-review.md)
- [Milestone 70 engineering review](docs/milestone-70-engineering-review.md)
- [Milestone 70 release report](docs/milestone-70-release-report.md)
- [Milestone 71 next capability selection](docs/milestone-71-next-capability-selection.md)
- [Milestone 71 architecture review](docs/milestone-71-architecture-review.md)
- [Milestone 71 engineering review](docs/milestone-71-engineering-review.md)
- [Milestone 72 conversation organisation proposal](docs/milestone-72-conversation-organisation-proposal.md)
- [Milestone 72 implementation record](docs/milestone-72-implementation.md)
- [Milestone 72 acceptance record](docs/milestone-72-acceptance.md)
- [Milestone 72 release report](docs/milestone-72-release-report.md)
- [Milestone 73 daily-use validation](docs/milestone-73-conversation-organisation-daily-use-validation.md)
- [Milestone 74 capability-guidance proposal](docs/milestone-74-capability-guidance-proposal.md)
- [Milestone 74 architecture review](docs/milestone-74-architecture-review.md)
- [Milestone 74 engineering review](docs/milestone-74-engineering-review.md)
- [Milestone 74 implementation record](docs/milestone-74-implementation.md)
- [Milestone 74 acceptance record](docs/milestone-74-acceptance.md)
- [Milestone 74 release report](docs/milestone-74-release-report.md)
- [Milestone 75 next capability selection](docs/milestone-75-next-capability-selection.md)
- [Milestone 75 architecture review](docs/milestone-75-architecture-review.md)
- [Milestone 75 engineering review](docs/milestone-75-engineering-review.md)
- [Milestone 76 local project record proposal](docs/milestone-76-local-nova-project-record-proposal.md)
- [Milestone 76 implementation record](docs/milestone-76-implementation.md)
- [Milestone 76 acceptance record](docs/milestone-76-acceptance.md)
- [Milestone 76 release candidate report](docs/milestone-76-release-report.md)
- [Milestone 77 knowledge-gap correction](docs/milestone-77-knowledge-gap-correction.md)
- [Milestone 78 architecture review](docs/milestone-78-architecture-review.md)
- [Milestone 78 engineering review](docs/milestone-78-engineering-review.md)
- [Milestone 78 implementation and status](docs/milestone-78-status.md)
- [Milestone 78 acceptance](docs/milestone-78-acceptance.md)
- [Milestone 78 release report](docs/milestone-78-release-report.md)
- [NOVA Conductor interaction north star](docs/conductor-interaction-north-star.md)
- [Milestone 69 implementation record](docs/milestone-69-implementation.md)
- [Milestone 69 architecture review](docs/milestone-69-architecture-review.md)
- [Milestone 69 engineering review](docs/milestone-69-engineering-review.md)
- [Milestone 69 acceptance](docs/milestone-69-acceptance.md)
- [Milestone 69 release report](docs/milestone-69-release-report.md)
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)
