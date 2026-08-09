# NOVA Repository Instructions

These instructions apply to the whole repository. Keep them concise enough for
Codex to load with any broader user or workspace instructions.

## Source-of-truth order

Before making claims or changes, inspect the current state instead of relying
on chat memory. Resolve conflicts in this order:

1. The current `JustAmanDoing/nova` GitHub repository: protected `main`, release
   tags, reviewed pull requests, and code.
2. Approved repository documents for architecture, engineering, roadmap,
   milestone status, operations, acceptance, and release evidence.
3. Reproducible verification results and the installed Windows NOVA runtime.
4. Explicit owner decisions recorded in the repository.
5. Chat discussions, which remain proposals until approved and recorded.

At the time this foundation was recorded, Milestone 78 was complete and
owner-accepted at Release 0.78.2, while Milestone 79 had not begun. Verify that
baseline before every later task because it will become historical.

## Architecture and product boundaries

- Keep NOVA local-first, privacy-first, owner-controlled, and useful without an
  AI provider.
- Preserve the modular monolith until measurements justify another boundary.
- Reuse the existing SQLite database, immutable knowledge revisions, checksums,
  append-only audit history, review workflows, backup and restore controls,
  Windows controls, and private Tailscale route.
- Do not create a second memory, knowledge store, task store, review queue,
  audit log, or source of truth when an existing NOVA component owns the data.
- AI may recommend or explain; it does not grant itself authority, approve its
  own actions, or silently make permanent knowledge.
- Keep material operations explicit, guarded, auditable, recoverable, and
  bounded to the approved scope.
- Never silently delete, overwrite, upload, share, publish, move, or expose
  owner data.
- Do not add an external AI provider, agent framework, plugin system, semantic
  search, autonomous filing, or broader network access without a separately
  approved architecture and engineering decision.

## Required development sequence

Follow [the development playbook](docs/development-playbook.md):

```text
Discuss -> Research/reuse check -> Architecture Review -> Engineering Review
-> Owner approval -> Codex implementation -> Verification -> Review -> PR/CI
-> Merge -> Install -> Owner acceptance -> Project-state update
```

Do not treat discussion, research, or an architecture proposal as
implementation approval. Do not begin the next runtime milestone merely
because its name appears in the roadmap.

## Reuse and current-capability policy

- Follow [NOVA Engineering Principles](docs/engineering-principles.md): reuse
  first and build last.
- Before custom-building a capability, verify what the current versions of
  ChatGPT, Codex, Codex Remote, GitHub, Docker, Tailscale, Ollama, Windows, and
  NOVA already provide.
- Use official current documentation, installed-version evidence, repository
  behavior, and a small proof where uncertainty matters.
- Prefer a proven free and open-source component only when it preserves NOVA's
  privacy, authority, recovery, and maintenance boundaries. A dependency is
  not automatically better than a small local integration.
- Record the options considered, the reuse decision, and why any custom code is
  still necessary in the engineering review.
- Never rewrite a working subsystem for novelty or preference.

## Phone-first Remote workflow

ChatGPT/Codex Remote on the owner's phone is the primary remote control surface
for development on the Windows PC. The owner physically verified Remote from
the phone against PC chats before this foundation was recorded.

- The phone starts, steers, approves, and reviews; the connected Windows PC
  performs repository, shell, Docker, browser, and runtime work.
- Remote inherits the PC chat's files, credentials, tools, sandbox, and
  approval boundaries. It does not expand them.
- Keep the host awake, online, signed in, and available while remote work runs.
- Design each phone-issued task around one outcome, a bounded scope, explicit
  constraints, objective verification, and a clear stopping point.
- Keep progress updates short and scannable. Make approval requests specific:
  state the action, target, impact, recovery path, and why approval is needed.
- Avoid requiring the owner to inspect large logs on the phone. Summarize the
  result and preserve detailed evidence in GitHub or repository documents.
- Use separate branches or worktrees for independent writing tasks; never let
  concurrent tasks edit the same files without coordination.

## Safe autonomous actions

Within an explicitly requested and approved engineering task, Codex may:

- inspect repository, GitHub, documentation, installed versions, and read-only
  runtime state;
- research current platform capabilities and reusable solutions;
- create a focused plan and make reasonable, reversible assumptions;
- create or use the approved branch or worktree;
- edit only in-scope files and preserve unrelated owner changes;
- add or update tests and documentation;
- run proportionate lint, type, test, build, security, Windows-control,
  Compose, and isolated-runtime checks;
- diagnose failures and correct in-scope defects;
- commit completed work; and
- push or update a draft pull request when repository publication is explicitly
  part of the task.

Autonomy does not broaden product scope or action authority.

## Actions requiring owner approval

Stop and obtain explicit owner approval before:

- accepting a product architecture or engineering scope;
- moving a draft pull request to ready when owner review is the gate;
- merging into protected `main`;
- creating a release or tag, installing an update, or changing the live Windows
  runtime;
- enabling a new external service, provider, production dependency, account,
  credential, plugin, agent, or paid capability with material authority;
- changing Tailscale exposure, enabling Funnel, opening ports, or weakening an
  authentication or browser boundary;
- performing a database migration outside an approved implementation, restore,
  destructive cleanup, permanent deletion, overwrite, bulk move, or data
  import;
- uploading, sharing, publishing, or sending owner data outside its approved
  local/private boundary; or
- expanding an approved task into a materially different capability.

Never merge, release, install, delete material data, or widen network exposure
merely because tests pass.

## Required verification

Verification is proportional to risk and must prove the changed boundary:

- documentation-only: final diff review, whitespace checks, link/path checks,
  repository-scope inspection, and protected CI;
- backend: Ruff, strict mypy, focused tests, complete pytest suite, and coverage;
- frontend: lint, type checking, focused tests, complete tests, and production
  build;
- Windows controls: `scripts/Test-NovaScripts.ps1`;
- deployment: Compose configuration, image build, isolated production runtime,
  non-root process, health, security headers, loopback binding, private Serve,
  and Funnel-off checks as applicable;
- data changes: migration, integrity, backup, restore, interruption, audit, and
  rollback evidence; and
- user-facing work: PC and phone-sized review plus physical owner acceptance
  when the capability depends on those environments.

Do not report a check as passed without authoritative output. A pending CI job
is pending, not passed.

## Completion and state reporting

Every completion report must include:

- exactly what changed and the important files;
- checks passed and any checks not run;
- unresolved issues, limitations, and risks;
- the resulting commit hash;
- branch and pull-request state;
- current project completion estimate; and
- one exact next action.

At the end of each completed work session, update the relevant repository
status, approved decisions, release and commit evidence, unresolved issues, and
exact next milestone. Do not rewrite historical evidence to describe an
unmerged candidate as released or installed.
