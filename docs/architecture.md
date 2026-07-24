# Nova Architecture

## Purpose

Nova begins as a local-first system design comparison tool. Its first architectural goal is a dependable browser-to-API vertical slice that can later support structured requirements, competing designs, trade-off scoring, explainable recommendations, approvals, and audit history.

## Current shape

```text
Browser
  └── React + TypeScript
        └── HTTP/JSON
              └── FastAPI
                    └── Versioned API routes
```

The repository is a monorepo, but the applications remain independently buildable and deployable.

## Boundaries

### Frontend

- Presents workspaces, comparisons, evidence, and approvals.
- Owns interaction state, not authoritative project data.
- Uses a single typed API adapter.

### Backend

- Owns business rules, validation, persistence, and provider integration.
- Exposes versioned endpoints under `/api/v1`.
- Keeps AI providers behind optional adapters so core workflows remain usable without them.

## Configuration

Runtime configuration comes from environment variables. `.env.example` contains safe defaults; populated `.env` files must never be committed.

## Security baseline

- Explicit CORS origins
- No secrets in source control
- Non-root backend container
- Minimal production images
- Health checks for orchestration
- AI providers disabled until explicitly configured

Authentication, authorization, persistence, and secret management will be introduced with the first feature that requires them, rather than guessed upfront.

## Evolution rules

1. Build complete vertical slices.
2. Keep recommendations explainable.
3. Require approval before material actions.
4. Preserve an audit path.
5. Add infrastructure only from measured need.

