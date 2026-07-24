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

## Milestone 1 — Observe — complete

- Read-only local intake folder
- Background and manual scanning
- File metadata and SHA-256 fingerprinting
- Exact-duplicate detection
- Local SQLite inventory
- Intake dashboard

## Milestone 2 — Understand — in progress

- Extract text from TXT and Markdown — complete
- Store normalized title, preview, counts, status, and evidence — complete
- Show understanding results in the dashboard — complete
- Enforce a configurable local extraction size limit — complete
- Add PDF and DOCX extraction — complete
- Keep understanding and recommendation processing local and read-only — complete
- Add local OCR for scanned PDFs and images

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

## Milestone 5 — Learn and advanced search

- Learn patterns only from confirmed approvals
- Semantic and ranked search
- User-controlled automation rules
- Measured thresholds before any automatic filing

## Later capabilities

- Optional local or cloud AI provider adapters
- Project and personal memory with source references
- Plugin and agent interfaces
- Backup, recovery, and operational hardening
