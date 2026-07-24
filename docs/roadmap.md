# Nova Roadmap

## Foundation — complete

- FastAPI and React monorepo
- Typed, versioned API and health checks
- Docker Compose local environment
- Backend and frontend tests
- Reproducible Node 20 and pnpm 9.15.5 build

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
- Add PDF and DOCX extraction
- Keep all processing local and make no file changes

## Milestone 3 — Recommend

- Deterministic rules before AI
- Suggest a category, filename, and destination
- Include confidence and a plain-language explanation
- Return no recommendation when evidence is insufficient

## Milestone 4 — Approve and execute

- Approval queue with edit, reject, and ignore actions
- Rename and move only after approval
- Append-only action audit
- Reversible execution and undo

## Milestone 5 — Learn and search

- Learn patterns only from confirmed approvals
- Metadata and full-text search
- User-controlled automation rules
- Measured thresholds before any automatic filing

## Later capabilities

- Optional local or cloud AI provider adapters
- Project and personal memory with source references
- Plugin and agent interfaces
- Backup, recovery, and operational hardening
