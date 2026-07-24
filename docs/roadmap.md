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
- Keep all processing local and make no file changes
- Add local OCR for scanned PDFs and images

## Milestone 3 — Recommend — complete

- Deterministic rules before AI — complete
- Suggest a category, approved-format filename, and destination — complete
- Include confidence and a plain-language explanation — complete
- Return no recommendation when evidence is insufficient — complete
- Recalculate after source, understanding, duplicate-status, or rule-version changes — complete
- Keep all recommendations read-only with no action controls — complete

## Milestone 4 — Approve and execute

- Approval queue with edit, reject, and ignore actions
- Rename and move only after approval
- Append-only action audit
- Reversible execution and undo

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
