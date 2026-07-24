# Nova

Nova is a local-first personal AI foundation that begins with safe, explainable
file intake. Its core remains useful without an AI provider.

The current MVP can:

- Observe files placed in a local intake folder
- Record filename, path, size, timestamps, and SHA-256 fingerprint
- Detect exact duplicates without deleting either copy
- Store the inventory in local SQLite
- Display intake status in a responsive local dashboard
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

Place a test file in `data/intake`. Nova scans automatically every three seconds,
or you can select **Scan now** in the dashboard. The folder is mounted read-only
inside the backend container.

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
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)
