# Nova Roadmap

## Foundation — complete

- FastAPI and React monorepo
- Typed, versioned API and health checks
- Docker Compose local environment
- Backend and frontend tests
- Reproducible Node 20 and pnpm 9.15.5 build
- Structured extraction diagnostics
- Filename, extracted-text, evidence, and metadata/status search
- Resilient background scanning and per-file parser isolation
- Stale inventory reconciliation and stable unfiltered dashboard totals
- Independent source-file and expanded-text safety limits
- Ordered, recorded, transactional SQLite schema migrations
- Double-click Windows start, stop, status, and guarded update controls
- Automatic backend, frontend, Windows-control, and production-container checks
- Browser-integrity guard on every state-changing local API request
- Read-only storage, database-size, and intake-scan health measurements
- Isolated production startup, dashboard, API, and intake smoke verification
- Local Host validation and restrictive dashboard browser security headers
- Portable bind-mount initialization with an immediate application privilege drop
- Keyboard-visible focus, live status announcements, and accessible intake table context
- Startup rejection of overlapping intake, library, backup, and database paths
- Non-overlapping dashboard refresh that pauses while the page is hidden
- Current supported Starlette `httpx2` test transport without deprecation warnings
- Cross-platform Python dependency constraints used by CI and production builds
- Automatic bounded container diagnostics after a failed Windows startup
- Read-only active-database integrity verification before migrations
- Explicit `no-store` policy for every API response
- Dashboard entry-page revalidation after application updates
- Patched pytest and Vitest toolchains with an advisory-clean resolved lock set
- Immutable commit pinning for every external GitHub Actions dependency
- Isolated production verification of approval, move, audit, undo, backup, and
  restore boundaries
- Git-enforced Linux entrypoint line endings with Windows-runner verification
- Runtime detection of source and container version drift on Windows
- Verified online database snapshot before a running Windows deployment updates
- Explicit loopback readiness probes with a diagnostic three-minute startup window
- Public-repository ignore rules, private vulnerability reporting, and tracked-file checks
- Immutable verified digests for all production container base images
- Representative production acceptance across TXT, Markdown, DOCX, PDF, image
  OCR, search, learning refresh, move, undo, backup, and restore
- Early storage capacity guidance in the dashboard and Windows status controls

## Milestone 1 — Observe — complete

- Read-only local intake folder
- Background and manual scanning
- File metadata and SHA-256 fingerprinting
- Exact-duplicate detection
- Local SQLite inventory
- Intake dashboard

## Milestone 2 — Understand — complete

- Extract text from TXT and Markdown — complete
- Store normalized title, preview, counts, status, and evidence — complete
- Show understanding results in the dashboard — complete
- Enforce a configurable local extraction size limit — complete
- Add PDF and DOCX extraction — complete
- Keep understanding and recommendation processing local and read-only — complete
- Add local OCR for scanned PDFs and images — complete

## Milestone 3 — Recommend — complete

- Deterministic rules before AI — complete
- Suggest a category, approved-format filename, and destination — complete
- Include confidence and a plain-language explanation — complete
- Return no recommendation when evidence is insufficient — complete
- Recalculate after source, understanding, duplicate-status, or rule-version changes — complete
- Keep all recommendations read-only with no filesystem action controls — complete

## Milestone 4 — Approve, execute, and audit — complete

- Approval queue with approve, edit, reject, ignore, and review-again actions — complete
- Persist review state against the exact recommendation version — complete
- Return changed recommendations to the queue — complete
- Validate edited filename and destination values — complete
- Keep approval separate from execution — complete
- Move into the library only after current approval and separate confirmation — complete
- Refuse overwrite, changed sources, stale approvals, and unsafe paths — complete
- Reverify SHA-256 immediately before source removal — complete
- Append-only operation event audit — complete
- Reversible execution and guarded undo — complete

## Operational hardening — recovery diagnostics — complete

- Detect operations left in `started` state beyond a safety delay — complete
- Reinspect source and destination paths without changing them — complete
- Compare current files with the recorded SHA-256 — complete
- Distinguish safe retry, likely completion, duplicate copy, conflict, missing,
  unsafe-path, and unreadable outcomes — complete
- Surface clear manual-review guidance in the dashboard — complete
- Keep all recovery assessment read-only — complete
- Create consistent, integrity-checked database backups — complete
- Store backups outside the Docker database volume — complete
- Bind the local deployment to the loopback interface — complete
- Add an explicit verified restore workflow — complete

## Milestone 5 — Learn and advanced search

- Learn preferred destinations only from successful confirmed moves — complete
- Invalidate a learning example when its move is undone — complete
- Keep learned suggestions behind explicit approval and execution — complete
- Inspect and explicitly forget stored learning groups — complete
- Deterministic multi-term and phrase-aware ranked search — complete
- Semantic search
- User-controlled automation rules
- Measured thresholds before any automatic filing

## Later capabilities

- Optional local or cloud AI provider adapters
- Project and personal memory with source references
- Plugin and agent interfaces
- Broader operational monitoring and disaster recovery
