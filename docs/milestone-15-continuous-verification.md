# Milestone 15: Continuous verification

## Outcome

Nova now verifies every proposed change and every update to `main` in GitHub
Actions. The checks mirror the supported local development paths and include a
full production-container build.

## Automatic checks

The workflow runs four independent jobs:

1. **Backend quality**
   - installs Python 3.12 dependencies from `backend/pyproject.toml` under
     `backend/constraints.txt`
   - runs Ruff
   - runs strict mypy
   - runs the complete pytest suite with the existing coverage threshold
2. **Frontend quality**
   - uses Node.js 20
   - activates the same pinned pnpm 9.15.5 version used by the Dockerfile
   - installs from the committed lockfile
   - runs ESLint, TypeScript, Vitest, and the production Vite build
3. **Windows controls**
   - parses the shared PowerShell controller on a Windows runner
   - verifies every friendly launcher requests the intended action
4. **Container build**
   - validates the Compose configuration
   - builds both production images, including local OCR dependencies
   - launches both production services in an isolated runner
   - verifies the health and operational-status APIs
   - verifies the compiled dashboard is served
   - confirms a synthetic local intake file is indexed
   - captures container state and logs on failure
   - removes the isolated containers and database volume after every run

## Safety and reproducibility

- The workflow receives read-only repository permission.
- Checkout credentials are not persisted.
- It does not deploy, publish, alter releases, or use application secrets.
- Superseded runs on the same branch are cancelled to avoid wasted work.
- Every job has a time limit so a stalled dependency or build cannot run
  indefinitely.
- Node.js and pnpm match the documented local and container versions.

## Scope

This milestone adds verification only. It does not change Nova's intake,
recommendation, approval, execution, learning, or storage behavior.

The workflow runs for pull requests, pushes to `main`, and explicit manual
requests. Local checks remain documented for use before a commit or while
offline.
