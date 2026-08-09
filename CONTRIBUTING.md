# Contributing

## Principles

- Follow the repository-wide [NOVA instructions](AGENTS.md).
- Follow the approved [NOVA Engineering Principles](docs/engineering-principles.md):
  reuse first and build custom code only when necessary.
- Follow the complete [NOVA Development Playbook](docs/development-playbook.md).
- Keep Nova local-first and useful without an AI provider.
- Prefer small, end-to-end changes over speculative frameworks.
- Explain recommendations and preserve user control.
- Never commit secrets or personal data.

## Development workflow

1. Discuss the product need and non-goals.
2. Inspect current NOVA and platform capabilities, search proven free and
   open-source solutions, and record the reuse decision.
3. Complete architecture and engineering review.
4. Obtain explicit owner approval for implementation.
5. Use a focused branch or worktree and implement only the approved scope.
6. Add or update tests and documentation.
7. Run proportionate local, Windows, Compose, and runtime checks.
8. Review the complete diff before publishing it.
9. Open or update a draft pull request with rationale, risks, and evidence.
10. Require protected CI to pass on the current candidate.
11. Merge, release, or install only after explicit owner approval.
12. Record physical owner acceptance and update project state after installation.

On Windows, validate the friendly launchers with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-NovaScripts.ps1
```

GitHub Actions repeats the complete backend and frontend suites, validates the
Windows controls on Windows, and builds the Docker Compose services. Do not
merge a change while any required check is failing or pending. Passing checks
do not replace owner approval.

## Commit style

Use concise, imperative commit messages, for example:

```text
Add comparison workspace
```
