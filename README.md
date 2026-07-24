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
- Recover background monitoring after an individual scan or parser failure
- Reconcile removed files and duplicate ownership with the current intake folder
- Keep dashboard totals accurate while search filters are active
- Run automatic background scans or a manual scan

Nova does not rename, move, delete, upload, or share intake files.

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
dashboard. The folder is mounted read-only inside the backend container.

Nova currently extracts and locally indexes UTF-8 text, PDF text layers, and DOCX
document text. Scanned PDFs without a text layer remain empty until OCR is added.
Search is case-insensitive and runs against the local SQLite inventory; file
contents are never returned by the API.

Recommendations are local, deterministic, and read-only. The first rules cover
invoice and project documents. Nova stores a versioned result, exposes its
plain-language reasons in the dashboard, and deliberately returns **No
recommendation** when evidence is insufficient. A recommendation never renames
or moves a source file.

Approval is also read-only in the current release. Approving a recommendation
records your intent against that exact recommendation version; it does not
rename or move anything. Edited values are validated as safe relative paths,
and a changed recommendation automatically requires a fresh review.

Two independent limits protect local resources:

- `NOVA_MAX_TEXT_BYTES` limits the source file size accepted for extraction.
- `NOVA_MAX_EXTRACTED_TEXT_BYTES` limits expanded text from parsers such as PDF
  and DOCX, including compressed document content.

Stop Nova with:

```bash
docker compose down
```

The SQLite inventory remains in a Docker volume between restarts. Use
`docker compose down -v` only when you intentionally want to erase Nova's local
inventory.

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
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)
