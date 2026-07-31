# Milestone 68 - Architecture Review

**Review date:** 31 July 2026

**Review scope:** Implemented Owner-Approved Next Actions

**Decision:** Pass for protected integration; final release approval awaits
Windows-host evidence and owner acceptance

## Source-of-truth review

Next actions are deliberately separate from permanent personal knowledge:

```text
owner-submitted local form
        |
        v
guarded next_actions state
        +
append-only next_action_events
        |
        v
local Focus projection
```

Approved knowledge remains authoritative for personal facts, preferences,
projects, and goals. The action store neither edits nor replaces knowledge
records or Markdown revisions.

## Architecture findings

### Local-first and privacy-first

- All state remains in NOVA's existing local SQLite database.
- No upload, cloud service, telemetry, external task provider, or new network
  path is introduced.
- API responses use the existing no-store boundary.
- An unverifiable linked project exposes no stale title or content.

### Owner control

- NOVA creates an action only after an explicit local form submission.
- Create, complete, and reopen are separate guarded owner actions.
- No conversation, document, knowledge record, or model output can create an
  action automatically.
- Completion history is retained; no delete operation exists.

### Modular monolith

- One migration, one bounded service, one route module, typed schemas, and one
  Focus section are added inside the existing application.
- The existing database, backup, restore, Host, browser-intent, and UI patterns
  are reused.
- No service split, event bus, plugin surface, agent framework, scheduler, or
  dependency is introduced.

### AI optionality

- Listing and state transitions are deterministic.
- Project association uses the existing deterministic file-integrity
  verification.
- Ollama is not required to create, view, complete, or reopen an action.

### Reversibility and auditability

- Complete can be reversed with explicit reopen.
- Every accepted transition adds an immutable event.
- Verified backup and guarded restore preserve both current state and history.
- Invalid duplicate transitions return a precise conflict without adding an
  event.

## Scope review

The implementation contains no priority, progress, date, deadline, reminder,
recurrence, notification, automatic extraction, model planning, assignment,
collaboration, remote access, voice, plugin, agent, tool, web, or autonomous
execution capability.

## Risks and controls

| Risk | Control |
| --- | --- |
| NOVA invents work | Only explicit owner form input is accepted |
| Focus becomes a second knowledge store | Actions use separate tables and never mutate knowledge |
| Stale project content appears | Live active-record and SHA-256 verification; unavailable links hide content |
| Completion destroys history | No delete route; append-only events and reopen |
| Task scope expands silently | Minimal API contract and published exclusions |
| Ollama outage blocks planning | Action lifecycle contains no model dependency |

## Architecture judgement

The implementation preserves NOVA's local-first, privacy-first,
owner-controlled modular monolith. It is architecturally safe to enter
protected integration, but release approval remains conditional on exact-head
CI and Windows-host acceptance.
