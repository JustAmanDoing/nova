# Milestone 64 - Architecture Review

**Review date:** 30 July 2026

**Selected slice:** Milestone 65 - Active Projects and Goals Workspace

**Decision:** Approved as a bounded proposal; runtime work awaits owner
approval

## Existing components to reuse

- `KnowledgeService` already owns approved records, immutable revisions,
  retirement, checksum-bound Markdown files, verified snapshots, and knowledge
  quality.
- Existing `project` and `goal` kinds already have approved storage and user
  interface labels.
- The knowledge-health checklist already identifies missing active projects and
  current goals.
- Guided add-through-chat prompts already prepare project and goal statements
  without saving them automatically.
- The React application already renders record status and exposes guarded
  lifecycle controls.
- SQLite, FastAPI, React, Docker Compose, backups, and Windows controls already
  provide the required local platform.

No new process, database, provider, framework, or open-source dependency is
required.

## Proposed flow

1. A read-only planning overview requests only active, verified `project` and
   `goal` records.
2. The backend reuses the current knowledge path-containment and SHA-256
   verification boundary.
3. The interface displays projects and goals in separate sections with title,
   owner-approved content, last-updated date, and review state.
4. Empty sections explain the gap and link to the existing guided chat prompt.
5. Adding information still creates a pending review card.
6. Only **Approve & save** creates permanent knowledge.
7. Corrections and retirement continue through immutable revisions and exact
   confirmation.

## Preserved boundaries

- Only active owner-approved records appear.
- No model decides what is a project, goal, priority, status, or next action.
- No inferred completion percentage or invented deadline.
- No automatic task creation, scheduling, notification, or reminder.
- No calendar, email, web, plugin, agent, or external-provider access.
- No file move, edit, deletion, upload, sharing, or autonomous action.
- The interface remains loopback-only.
- Existing knowledge files and the SQLite record remain the authoritative
  sources.
- The modular monolith remains unchanged.

## Storage and API

The preferred first slice adds no schema migration. A small read-only planning
view may be derived from existing active knowledge records. If a dedicated API
response is useful, it should be a versioned endpoint backed by
`KnowledgeService`, not a new planning store.

The interface must not cache a second authoritative project or goal copy.

## Privacy

Project and goal content is personal information. It remains on the local
machine, is returned only through the existing loopback API, and receives the
same no-store HTTP policy as other private API responses. No content enters
Git, analytics, telemetry, or an external service.

## Architecture risks

- A dashboard could imply that displayed records are tasks with measured
  progress when they are only approved knowledge.
- A second editing flow could bypass immutable revisions or owner approval.
- A planning-specific store could duplicate the knowledge source of truth.
- Automatic prioritization could silently turn a display feature into an
  autonomous planner.

The bounded proposal prevents those shifts by making the first slice a
read-only projection over existing verified knowledge and reusing the current
lifecycle controls.

## Architecture judgement

The proposal is proportionate and has a stronger impact-to-complexity ratio
than the remaining candidates. It preserves local-first privacy, explicit owner
approval, existing sources of truth, recoverability, and the modular monolith.
It is approved for implementation only after explicit owner approval of the
Milestone 65 scope.
