# Milestone 67 - Architecture Review

**Review date:** 31 July 2026

**Selected slice:** Milestone 68 - Owner-Approved Next Actions

**Decision:** Pass with proposal conditions; runtime not approved

## Architectural fit

The selected slice fits the current modular monolith when next actions remain
a small, explicit, local state module rather than being represented as
permanent personal knowledge.

```text
owner-confirmed local form
          |
          v
local intent and validation guard
          |
          v
SQLite next-action state + append-only events
          |
          v
read-only Focus projection
```

The approved knowledge store remains authoritative for personal facts,
preferences, goals, and projects. Next actions have their own bounded lifecycle
because completion and reopening are operational state, not corrections to
permanent knowledge.

## Required architecture boundaries

### Local-first and private

- Store action data only in NOVA's existing local SQLite database.
- Serve the API and Focus interface through the existing loopback services.
- Add no upload, telemetry, cloud account, external provider, or network
  listener.

### Owner control

- Create an action only after explicit owner submission.
- Complete or reopen an action only after an explicit owner gesture.
- Do not infer actions from goals, projects, documents, or conversation.
- Do not rank, schedule, notify, or execute actions.
- Do not silently delete completed actions.

### Separation from knowledge

- Do not add a `task` or `next_action` knowledge kind merely to reuse
  retirement semantics.
- Keep approved project and goal records unchanged and integrity verified.
- An optional project association must reference a currently verified active
  project but must not modify that knowledge record.

### Modular monolith

- Add one bounded backend module, versioned local routes, schema migration,
  and Focus UI section inside the existing application.
- Add no second service, queue, scheduler, event bus, plugin surface, or agent
  framework.
- Prefer existing dependencies and patterns; add no dependency unless
  evidence proves it necessary.

### Auditability and recovery

- Store append-only create, complete, and reopen events.
- Include next-action state and history in existing database backups and
  restore verification.
- Use ordered migrations and preserve rollback/recovery evidence.

## Risks and controls

| Risk | Required control |
| --- | --- |
| NOVA invents work | Explicit owner entry only; no model-derived actions |
| Focus becomes a hidden automation surface | No scheduler, notification, tool, or execution authority |
| Tasks corrupt knowledge semantics | Separate SQLite state and event history |
| A stale project link misleads the owner | Verify the active project at read time and show an unavailable association safely |
| Completion destroys history | Append-only events and no silent deletion |
| Scope grows into a full task manager | Exclude dates, priorities, subtasks, recurrence, reminders, and integrations |

## Architecture judgement

The proposal is compatible with NOVA's local-first, privacy-first,
owner-controlled modular monolith if all conditions above remain mandatory.
Architecture approval applies to the proposal only. Runtime implementation
still requires explicit owner approval.
