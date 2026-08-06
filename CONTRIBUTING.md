# Contributing

## Principles

- Follow the approved [NOVA Engineering Principles](docs/engineering-principles.md):
  reuse first and build custom code only when necessary.
- Keep Nova local-first and useful without an AI provider.
- Prefer small, end-to-end changes over speculative frameworks.
- Explain recommendations and preserve user control.
- Never commit secrets or personal data.

## Development workflow

1. Search for proven free, open-source solutions and record the reuse decision.
2. Create a focused branch.
3. Add or update tests with the implementation.
4. Run the relevant backend and frontend checks.
5. Document behavior changes.
6. Open a pull request with the rationale and validation results.

On Windows, validate the friendly launchers with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-NovaScripts.ps1
```

GitHub Actions repeats the complete backend and frontend suites, validates the
Windows controls on Windows, and builds the Docker Compose services. Do not
merge a change while any required check is failing.

## Commit style

Use concise, imperative commit messages, for example:

```text
Add comparison workspace
```
