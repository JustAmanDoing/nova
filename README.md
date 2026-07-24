# Nova

Nova is a local-first personal AI foundation that begins with safe, explainable
file intake. Its core remains useful without an AI provider.

The current MVP can:

- Observe files placed in a local intake folder
- Record filename, path, size, timestamps, and SHA-256 fingerprint
- Detect exact duplicates without deleting either copy
- Extract TXT, Markdown, PDF, and DOCX content locally
- Record a title, short preview, word count, and extraction evidence
- Mark empty, oversized, failed, and not-yet-supported files clearly
- Store the inventory in local SQLite
- Display intake status in a responsive local dashboard
- Search filenames, paths, extracted text, titles, evidence, and extraction errors
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
- Recover background monitoring after an individual scan or parser failure
- Reconcile removed files and duplicate ownership with the current intake folder
- Keep dashboard totals accurate while search filters are active
- Run automatic background scans or a manual scan

Nova never moves a file automatically and never overwrites an existing file.
It does not upload, share, or permanently delete documents.

## Quick start with Docker

Prerequisite: Docker Desktop with Docker Compose.

```bash
docker compose up --build
```

Open:

- Nova: http://localhost:5173
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/api/v1/health

Place a TXT, Markdown, PDF, or DOCX test file in `data/intake`. Nova scans
automatically every three seconds, or you can select **Scan now** in the
dashboard. The local `data` root is mounted into the backend; scans remain
read-only, while an explicitly confirmed move can place an approved file under
`data/library`.

Nova currently extracts and locally indexes UTF-8 text, PDF text layers, and DOCX
document text. Scanned PDFs without a text layer remain empty until OCR is added.
Search is case-insensitive and runs against the local SQLite inventory; file
contents are never returned by the API.

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

Two independent limits protect local resources:

- `NOVA_MAX_TEXT_BYTES` limits the source file size accepted for extraction.
- `NOVA_MAX_EXTRACTED_TEXT_BYTES` limits expanded text from parsers such as PDF
  and DOCX, including compressed document content.

Stop Nova with:

```bash
docker compose down
```

The SQLite inventory and action audit remain in a Docker volume between
restarts. Filed documents remain on disk under `data/library`. Use
`docker compose down -v` only when you intentionally want to erase Nova's local
inventory and audit; it does not remove filed documents.

## Local development

### Backend

Requires Python 3.12+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
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
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)
