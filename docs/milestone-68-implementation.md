# Milestone 68 - Owner-Approved Next Actions

**Implementation date:** 31 July 2026

**Base release:** 0.65.0

**Target release:** 0.68.0

**Branch:** `agent/milestone-68-owner-approved-next-actions`

**Status:** Complete; release 0.68.0 integrated, installed, recovery-tested,
and accepted by the owner

## Outcome

NOVA now provides a small local next-action lifecycle beside the verified
projects and goals on Focus. The owner must type and submit every action.
NOVA does not extract, generate, rank, schedule, or execute actions.

## Backend implementation

- Ordered database migration 16 creates `next_actions` and append-only
  `next_action_events`.
- Actions support only `open` and `completed`.
- Explicit create, complete, and reopen operations use NOVA's existing
  local-browser intent guard.
- Completed actions remain stored and recoverable. There is no delete route.
- Each accepted transition records a created, completed, or reopened event.
- Titles are normalized and limited to 200 characters.
- Optional project association accepts only an active project that passes the
  existing approved-file path and SHA-256 verification boundary.
- A retired, missing, or checksum-invalid association returns no project title
  or content and is marked unavailable.
- Read-only event history makes the lifecycle locally auditable.

## API contract

- `GET /api/v1/focus/actions`
- `POST /api/v1/focus/actions`
- `POST /api/v1/focus/actions/{id}/complete`
- `POST /api/v1/focus/actions/{id}/reopen`
- `GET /api/v1/focus/actions/{id}/events`

The contract contains no priority, score, progress, due date, deadline,
schedule, recurrence, reminder, notification, assignee, tool, or execution
field.

## Frontend implementation

- Focus loads verified direction and next actions independently.
- Existing verified data remains visible if a refresh fails.
- A semantic local form accepts one title and an optional verified project.
- Open actions provide an explicit **Mark complete** control.
- Completed history is retained in a disclosure with an explicit **Reopen**
  control.
- Pending, success, failure, empty, unavailable, and stale-association states
  are stated truthfully.
- Responsive layout, labelled native controls, focus indicators, and status or
  alert regions preserve keyboard and narrow-screen operation.

## Recovery and operational impact

- The action tables live in the existing SQLite database.
- Existing verified database backup and guarded restore include both action
  state and event history without a second recovery system.
- Startup migration remains transactional and refuses newer or inconsistent
  schemas.
- No dependency, external service, background worker, model requirement, or
  network authority was added.

## Version alignment

Backend and frontend target versions are aligned at `0.68.0`.

## Explicit exclusions

This implementation does not add automatic task capture, model-generated
plans, priorities, dates, deadlines, reminders, recurrence, notifications,
calendar or email integration, voice, remote access, semantic retrieval,
plugins, agents, tools, web access, autonomous execution, or deletion of
action history.

## Release evidence

- Implementation commit:
  `8888969a956c0c1bb4171aa977ac52c5be0b9a4c`
- Implementation merge commit:
  `d74d8ec0e31eaa1774239a6443f76c10f32d70df`
- PR #11 protected verification: pass
- Merged-main protected verification: pass
- Windows production migration, runtime, privacy, responsive layout, guarded
  backup and restore, and owner lifecycle acceptance: pass

Detailed evidence is recorded in:

- `docs/milestone-68-acceptance.md`
- `docs/milestone-68-release-report.md`
