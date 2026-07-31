# Milestone 67 - Engineering Review

**Review date:** 31 July 2026

**Selected slice:** Milestone 68 - Owner-Approved Next Actions

**Decision:** Feasible and bounded; runtime not approved

## Reuse review

The implementation can reuse:

- ordered SQLite migrations and startup migration records;
- the existing database service and backup/restore boundary;
- local browser-intent and Host validation controls;
- append-only event patterns used by guarded operations;
- the verified active-project projection;
- Focus loading, refresh, failure-preservation, and responsive UI patterns;
- existing API schemas, route organization, tests, and coverage gates;
- Windows controllers and protected GitHub verification.

No new service or third-party runtime dependency is justified.

## Proposed implementation sequence

1. Add one ordered migration for next-action state and append-only events.
2. Add typed schemas for create, list, complete, and reopen operations.
3. Add a bounded service enforcing title limits, state transitions, and
   optional verified-project association.
4. Add versioned local routes protected by the existing browser-intent guard.
5. Extend Focus with open and recently completed action sections.
6. Add explicit create, complete, and reopen controls with truthful failure
   states.
7. Extend backup, restore, migration, and representative-runtime tests.
8. Run protected pull-request, post-merge, Windows-host, privacy, accessibility,
   recovery, and owner acceptance.

## Engineering constraints

- The owner supplies the action text; no model extraction is permitted.
- Action titles must be plain text with a documented size limit.
- The first release supports only `open` and `completed` states.
- Complete and reopen must be idempotent or return a precise conflict.
- Completed actions remain locally auditable.
- An invalid, retired, missing, or checksum-failed project association must not
  expose unverified project content.
- Focus must remain useful if Ollama is unavailable.
- No date, priority, reminder, recurrence, notification, automatic ordering,
  or execution field may enter the first API contract.
- No source file, personal knowledge file, or document is changed by an action
  transition.

## Test obligations

Backend tests must cover:

1. explicit action creation;
2. input and browser-intent rejection;
3. deterministic open/completed listing;
4. complete and reopen event history;
5. invalid transition behavior;
6. optional verified-project association;
7. stale or unverifiable project-association handling;
8. migration from the accepted 0.65.0 database;
9. backup and restore preservation; and
10. no knowledge-record mutation.

Frontend tests must cover:

1. truthful empty state;
2. explicit create flow;
3. pending and failed writes;
4. complete and reopen flows;
5. failed refresh preserving last verified state;
6. responsive and keyboard-accessible controls;
7. no invented priority, progress, date, or next step; and
8. usability without Ollama.

## Delivery estimate

The bounded implementation is a small-to-medium local feature. Most work is
state-transition correctness, audit evidence, recovery coverage, and owner
acceptance rather than visual complexity.

Target runtime version if approved: 0.68.0.

## Engineering judgement

Milestone 68 is implementable without weakening NOVA's architecture or adding
external dependencies. The proposal is ready for an owner decision. No source,
migration, API, frontend, version, or runtime change is authorized by this
review.
