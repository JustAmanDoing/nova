# Milestone 64 - Engineering Review

**Review date:** 30 July 2026

**Selected slice:** Milestone 65 - Active Projects and Goals Workspace

**Decision:** Feasible and recommended; implementation awaits owner approval

## Feasibility findings

The current implementation already provides the important primitives:

- `goal` and `project` are valid typed knowledge kinds;
- active and retired records are already listed;
- approved Markdown files are path-contained and checksum-bound;
- lifecycle updates already create immutable revisions;
- retirement already uses exact confirmation and preserves history;
- knowledge quality already calculates missing and review-due states;
- guided prompts already exist for active projects and current goals; and
- the frontend already renders knowledge records and guarded lifecycle
  controls.

The first slice requires no new dependency and should not require a database
migration.

## Required implementation areas

### Backend

- Add a bounded read-only method that returns active, currently verified
  `project` and `goal` records.
- Reuse current path-containment and live SHA-256 verification.
- Include last-updated and deterministic review-state metadata.
- Return a truthful empty section when no qualifying record exists.
- Keep failed or stale records out of the active overview and surface a safe
  warning rather than silently trusting them.

### Frontend

- Add a clearly labelled **Focus** or **Projects & goals** view.
- Separate active projects from current goals.
- Display owner-approved title and content, updated date, and review state.
- Reuse **Add through chat** for empty or review-due sections.
- Reuse existing edit and retire lifecycle controls rather than creating a
  second write path.
- State explicitly that NOVA is not estimating progress or choosing priorities.
- Provide keyboard, screen-reader, narrow-window, and zoom-safe behavior.

### Documentation and operations

- Document the deterministic, read-only-first boundary.
- Keep runtime, backend, and frontend versions aligned if implementation is
  approved.
- Preserve the supported start, status, update, backup, restore, and knowledge
  snapshot workflows.

## Required tests

1. Active verified projects appear only in the project section.
2. Active verified goals appear only in the goal section.
3. Retired records do not appear.
4. Missing, outside-root, or checksum-mismatched knowledge does not appear.
5. A verification failure produces a safe local warning.
6. Empty sections show the correct guided chat action.
7. Preparing a guided prompt stores nothing.
8. Approving a project or goal makes it appear after refresh.
9. Updating creates a new immutable revision and refreshes the overview.
10. Retiring removes the item from the active overview without deleting
    history.
11. No progress percentage, priority, deadline, or next action is inferred.
12. Existing chat, knowledge, intake, backup, and restore behavior remains
    unchanged.
13. Backend coverage remains at least 90%.
14. Frontend lint, typing, tests, production build, accessibility, and reflow
    checks pass.
15. The isolated production workflow and Windows-host acceptance pass.

## Delivery assessment

The change is a small projection and focused interface over existing knowledge
records. A careful implementation should fit one bounded milestone and reuse
the current application structure.

## Risks

- Personal planning information is sensitive.
- The view could accidentally imply stale records are current.
- Duplicate editing logic could weaken lifecycle controls.
- A visually polished board could overstate NOVA's planning intelligence.
- Scope could expand into task management, calendar integration, or autonomous
  prioritization.

Loopback-only delivery, current-hash verification, freshness indicators,
existing lifecycle controls, explicit wording, and strict scope exclusions
bound these risks.

## Engineering judgement

Milestone 65 is ready for an owner decision. No implementation, version change,
migration, runtime rebuild, or release is authorized by this review.
