# Nova

Nova is a local-first foundation for comparing AI system designs and evolving them into explainable, testable recommendations.

This repository starts with a production-shaped monorepo:

- FastAPI backend with versioned API routes and health checks
- React frontend built with Vite and TypeScript
- Docker Compose for a one-command local environment
- Tests, linting, typed configuration, and structured documentation
- Clear boundaries for future comparison, recommendation, and audit features

## Quick start with Docker

Prerequisites: Docker Desktop with Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Web app: http://localhost:5173
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/api/v1/health

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

Requires Node.js 20+.

```bash
cd frontend
corepack enable
pnpm install
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
├── backend/            FastAPI application and tests
├── frontend/           React/Vite application and tests
├── docs/               Architecture and roadmap
├── .env.example        Safe local configuration template
└── docker-compose.yml  Local full-stack environment
```

## Current capability

The frontend calls the backend health endpoint and displays live service status. This intentionally small vertical slice proves the complete browser-to-API path before Nova gains comparison workflows.

## Safety

Never commit secrets, API keys, private documents, personal data, or a populated `.env` file. Nova's core is designed to work without an AI provider; provider integrations will be optional and explicitly configured.

## Documentation

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)
