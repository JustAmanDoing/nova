# Milestone 65 - Active Projects and Goals Workspace

**Implementation date:** 30 July 2026

**Base release:** 0.63.0

**Target release:** 0.65.0

**Branch:** `agent/milestone-65-active-projects-goals`

**Status:** Implemented; protected pull-request and Windows-host acceptance
remain pending

## Outcome

NOVA now has a separate local **Focus** workspace for the projects and goals
the owner explicitly approved as permanent knowledge. The workspace remains a
read-only projection over the existing knowledge source of truth.

## Backend implementation

- Added `GET /api/v1/knowledge/planning`.
- Selects only active records whose candidate is approved and whose kind is
  `project` or `goal`.
- Reuses the existing path-containment and live SHA-256 verification boundary.
- Excludes records that cannot be verified and reports only a safe aggregate
  count and warning.
- Separates projects from goals.
- Returns owner-approved title and content, revision, update time, review due
  time, and deterministic review state.
- Uses a fixed 90-day review interval. A verified older record remains visible
  and is labelled **Review due**.
- Does not infer progress, priority, dates, deadlines, plans, tasks, or next
  actions.

## Frontend implementation

- Added `/focus.html` as a separate production entry point.
- Added navigation between Intake, Chat, and Focus.
- Displays separate active-project and current-goal sections.
- Displays verified count, safe exclusion warnings, revision, last update, and
  review state.
- Uses truthful loading, empty, unavailable, and failed-refresh states.
- An empty section links to the existing guided chat workflow. The handoff
  prepares an editable prompt but does not send or save it.
- A record review link opens the existing immutable update and guarded
  retirement controls.
- The page remains useful without Ollama because its projection is
  deterministic and local.

## Data and migration impact

- No database migration.
- No new permanent store.
- No project or task database.
- No new dependency.
- Existing approved Markdown revisions and SQLite lifecycle records remain the
  authority.

## Version alignment

Backend and frontend versions are aligned at `0.65.0`.

## Verification completed before pull request

- backend lint;
- backend static typing;
- complete backend test suite and coverage;
- frontend lint;
- frontend static typing;
- complete frontend test suite;
- multi-entry production frontend build;
- patch whitespace validation; and
- focused tests for projection filtering, integrity failure, freshness,
  truthful empty states, unavailable state, and guarded chat handoff.

The exact test counts and Windows-host result will be recorded in the final
release report after protected integration and local acceptance.

## Explicit exclusions

This milestone does not add tasks, automatic project discovery, inferred
progress, priorities, dates, deadlines, reminders, calendar, email,
automation, semantic search, remote access, voice, plugins, agents, tools, web
access, or external providers.
