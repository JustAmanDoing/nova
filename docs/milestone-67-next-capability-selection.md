# Milestone 67 - Evidence-Led Next Capability Selection

**Completion date:** 31 July 2026

**Base release:** 0.65.0

**Decision:** Complete; Milestone 68 Owner-Approved Next Actions selected,
runtime implementation not yet approved

## Objective

Choose the next bounded capability in order of owner impact while preserving
NOVA's local-first privacy, owner control, recoverability, AI optionality, and
modular-monolith architecture.

## Evidence used

- Milestone 66 validated genuine project and goal capture, Focus display, and
  immutable correction behavior.
- Focus now exposes one verified active project and one verified current goal
  with no integrity exclusions.
- The owner accepted the Focus page as useful, clear, and non-intrusive.
- Focus deliberately does not store or infer tasks, progress, priority,
  deadlines, or next actions.
- The owner's current approved direction emphasizes everyday planning and
  knowledge management.
- Knowledge health reports 50% weighted core coverage, 100% freshness, and
  100% retrieval self-check quality.
- Four core profile areas remain missing, but the existing Knowledge health,
  Add through chat, review, approval, revision, and retrieval paths already
  provide a safe way to add them. Another runtime feature is not required for
  that work.
- Explicit single-document context already works. Current evidence does not
  yet justify broad automatic or semantic retrieval.
- Remote access, calendar integration, reminders, voice, plugins, agents, and
  external providers remain distinct risk decisions.

No personal record content is copied into this decision document.

## Impact-first selection method

Candidates were scored from 1 to 5. Owner impact and direct evidence of an
unmet need contribute 60% of the result:

- practical owner impact: 40%;
- evidence of a current unmet need: 20%;
- fit with the existing architecture: 15%;
- privacy and safety: 10%;
- reuse of verified NOVA components: 10%; and
- delivery and maintenance simplicity: 5%.

The score is a transparent comparison aid, not a claim of mathematical
certainty.

| Rank | Candidate | Impact | Evidence | Fit | Safety | Reuse | Delivery | Weighted |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Owner-approved next actions | 5 | 5 | 4 | 5 | 4 | 3 | 4.65 |
| 2 | Guided completion of remaining core knowledge | 4 | 5 | 5 | 5 | 5 | 5 | 4.60 |
| 3 | Explicit filed-library document context | 5 | 3 | 5 | 4 | 5 | 4 | 4.45 |
| 4 | Broad semantic document search | 5 | 3 | 3 | 3 | 2 | 2 | 3.65 |
| 5 | Secure phone access to NOVA | 5 | 3 | 2 | 2 | 3 | 2 | 3.50 |
| 6 | Calendar and reminders | 5 | 3 | 2 | 2 | 2 | 2 | 3.40 |
| 7 | Voice conversation | 4 | 2 | 2 | 2 | 2 | 2 | 2.80 |

## Selected product slice

**Milestone 68 - Owner-Approved Next Actions**

Add a small local next-actions section to Focus. It stores only actions the
owner explicitly enters and confirms. The owner can optionally associate an
action with one currently verified active project, mark it complete, and
reopen it. Every state change is local and auditable.

The first slice is intentionally not a general task manager. It does not add
priorities, dates, reminders, recurrence, notifications, calendar sync,
automatic task discovery, model-generated plans, or autonomous execution.

## Why this is the most impactful next step

- It closes the direct gap between visible direction and owner-chosen action.
- It supports the owner's current everyday-planning objective.
- It builds on the Focus page that just passed real-world validation.
- It remains useful without Ollama or any external provider.
- Explicit owner entry avoids invented tasks and uncertain model extraction.
- Existing database migrations, local-intent guards, audit patterns, backup,
  restore, responsive UI, and protected verification can be reused.
- A bounded action list provides evidence before considering dates, reminders,
  calendars, prioritization, or automation.

## Why guided knowledge completion is not the selected build

It is nearly equal in impact, but NOVA already provides the complete safe
workflow. The owner can use existing high-value gap suggestions and Add
through chat without waiting for engineering work. Building another onboarding
path would duplicate an accepted capability.

## Why the other candidates are later

### Explicit filed-library document context

This remains the strongest document candidate. Current evidence favors daily
planning first, while explicit intake-document context already provides a
bounded document workflow.

### Broad semantic document search

It would expand implicit document access and introduce embedding models,
chunking, vector-index lifecycle, retrieval evaluation, and new privacy
decisions. Explicit selection remains the safer evidence path.

### Secure phone access

NOVA is deliberately loopback-only. Remote access needs authentication,
private transport, sessions, origin controls, recovery, and its own threat
model.

### Calendar and reminders

Scheduling adds time zones, recurrence, delivery reliability, notification
permissions, external account access, and missed-reminder risk. A stable
owner-controlled action lifecycle should come first.

### Voice

Voice adds microphone permissions, local speech recognition and synthesis,
interruption, retention, and likely remote-access dependencies.

## Decision boundary

Milestone 67 authorizes selection and proposal review only. It does not
authorize a database migration, API change, frontend change, runtime rebuild,
version bump, release, task import, notification, or external integration.

Milestone 68 runtime implementation requires explicit owner approval of
`docs/milestone-68-owner-approved-next-actions-proposal.md`.

## Completion estimate

- Accepted practical local NOVA prototype scope: 100%.
- Broader long-term NOVA vision: approximately 82%.
- Milestone 67 decision work: 100%.

## Exact next action

Obtain explicit owner approval for Milestone 68. If approved, implement only
the bounded owner-approved next-actions slice, verify it through the protected
workflow and Windows acceptance, and issue a release decision before selecting
another capability.
