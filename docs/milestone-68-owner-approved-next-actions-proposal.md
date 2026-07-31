# Milestone 68 Proposal - Owner-Approved Next Actions

**Proposal date:** 31 July 2026

**Base release:** 0.65.0

**Status:** Complete; bounded release 0.68.0 integrated, installed, and
accepted on 31 July 2026

## User outcome

NOVA gives the owner one calm local list of deliberately chosen next actions
beside verified projects and goals. It helps convert direction into action
without inventing priorities, deadlines, plans, or work.

## In scope

- one Next actions section on the existing Focus page;
- explicit owner entry through a small local form;
- short plain-text action title;
- `open` and `completed` states only;
- optional association with one currently verified active project;
- explicit complete and reopen controls;
- append-only local state-transition history;
- deterministic ordering and truthful empty states;
- local SQLite storage inside the existing database;
- existing browser-intent, Host, no-store, backup, restore, migration, audit,
  and recovery boundaries;
- responsive and keyboard-accessible interaction;
- backend, frontend, privacy, accessibility, recovery, and Windows acceptance;
  and
- protected pull-request and post-merge verification.

## Out of scope

- model-generated or automatically extracted actions;
- actions created from conversation, documents, goals, or projects without
  explicit form submission;
- priorities, scoring, ranking, progress, XP, streaks, or recommendations;
- due dates, deadlines, time estimates, schedules, recurrence, reminders, or
  notifications;
- subtasks, dependencies, boards, assignment, collaboration, or multiple
  owners;
- calendar, email, mobile, or external task-service integration;
- autonomous execution, background agents, tools, plugins, or web access;
- voice capture;
- semantic retrieval;
- permanent deletion of action history;
- changing a project or goal knowledge record; and
- any file move, edit, deletion, upload, sharing, or overwrite.

## Safety rules

1. NOVA creates an action only from explicit owner-submitted text.
2. NOVA must not infer an action from existing knowledge or model output.
3. Create, complete, and reopen are separate explicit state changes.
4. Every state change records an append-only local event.
5. Completed actions remain recoverable and auditable.
6. Optional project association displays only if the project remains active
   and integrity verified.
7. A failed project verification must not expose stale project content.
8. The action store must not modify or replace approved knowledge.
9. Focus must not imply priority, progress, deadline, or automatic ordering
   beyond a published deterministic rule.
10. No model, scheduler, notification service, network authority, or
    autonomous execution is added.

## Acceptance criteria

- architecture and engineering implementation reviews pass;
- all existing backend and frontend checks pass;
- backend coverage remains at least 90%;
- an owner can explicitly create, complete, and reopen an action;
- every transition is represented in local append-only history;
- open and completed actions appear in truthful sections;
- optional project association uses only a live verified active project;
- stale or unverifiable associations fail safely;
- migration, backup, restore, and database integrity pass;
- the implementation contains no priority, date, reminder, recurrence,
  notification, automatic extraction, or execution authority;
- local-only, no-store, privacy, security-header, unexpected-Host, and browser
  intent controls remain intact;
- protected checks pass on the exact pull-request head and merged `main`;
- the installed Windows release matches accepted `main`; and
- owner acceptance confirms the workflow is useful, clear, and non-intrusive.

## Approval boundary

Approval of this proposal would authorize only the bounded scope above. It
would not authorize calendars, reminders, notifications, automatic task
capture, model-generated planning, prioritization, scheduling, remote access,
voice, plugins, agents, tools, web access, or external providers.
