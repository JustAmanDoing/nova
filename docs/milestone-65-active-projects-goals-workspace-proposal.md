# Milestone 65 Proposal - Active Projects and Goals Workspace

**Proposal date:** 30 July 2026

**Base release:** 0.63.0

**Status:** Approved by the owner on 30 July 2026; implementation and
acceptance are in progress on a protected feature branch

## User outcome

NOVA gives the owner one calm local focus screen showing the projects and goals
the owner has explicitly approved. It makes important direction visible
without asking the model to invent plans, priorities, progress, or deadlines.

## In scope

- one local projects-and-goals focus view;
- separate active-project and current-goal sections;
- active, owner-approved, currently verified knowledge only;
- owner-approved title and content;
- last-updated and deterministic review-state visibility;
- truthful empty states;
- reuse of guided **Add through chat** prompts;
- reuse of existing immutable update and guarded retirement controls;
- read-only-first API projection over the existing knowledge source of truth;
- safe warnings for stale or unverifiable records;
- backend, frontend, accessibility, privacy, backup, recovery, and Windows
  acceptance; and
- protected pull-request and post-merge verification.

## Out of scope

- automatic project or goal discovery;
- model-generated projects, goals, priorities, plans, or next actions;
- progress percentages, scoring, streaks, XP, or achievements;
- task lists, subtasks, dependencies, boards, or notifications;
- dates, deadlines, reminders, calendar, email, or scheduling;
- automatic updates from conversation;
- autonomous execution or background agents;
- semantic search or automatic document retrieval;
- web access, plugins, remote access, voice, or external providers;
- a second project database; and
- any file move, edit, deletion, upload, sharing, or overwrite.

## Safety rules

1. A displayed item must be an active owner-approved knowledge record.
2. Its current Markdown path and SHA-256 must still verify.
3. Failed verification must not silently display stale content.
4. The overview must not infer completion, priority, dates, or next actions.
5. Preparing an add-through-chat prompt stores nothing.
6. Permanent additions still require **Approve & save**.
7. Corrections use immutable revisions.
8. Retirement preserves files, revisions, and audit history.
9. The local knowledge store remains the single source of truth.
10. No model, tool, network, or autonomous authority is added.

## Acceptance criteria

- architecture and engineering implementation reviews pass;
- all existing backend and frontend tests pass;
- backend coverage remains at least 90%;
- verified active projects and goals appear in the correct sections;
- retired and unverifiable records are excluded;
- empty and review-due states guide the owner without saving automatically;
- update and retirement behavior reuse the existing lifecycle;
- no inferred planning data appears;
- local-only, no-store, privacy, backup, snapshot, restore, and repository
  hygiene controls remain intact;
- protected checks pass on the exact pull-request head and merged `main`;
- the installed Windows release matches accepted `main`; and
- owner acceptance confirms the view is useful, truthful, and non-intrusive.

## Approval boundary

Approval of this proposal would authorize only the bounded scope above. It
would not authorize task management, calendars, reminders, autonomous
prioritization, automatic memory, semantic retrieval, remote access, voice,
plugins, agents, tools, web access, or external providers.
