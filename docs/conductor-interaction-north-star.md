# NOVA Conductor - Interaction North Star

**Decision date:** 6 August 2026

**Status:** Approved product direction; not implementation authorization

## Purpose

The NOVA Conductor is the single conversational interface between the owner
and NOVA. The owner should experience one continuous assistant through text or
voice without having to select an internal service or specialist.

The Conductor is an interaction and orchestration boundary. It does not replace
the domain authority, approval rules, audit history, or recovery controls of
NOVA's existing services.

## Owner experience

The Conductor should:

- hold natural, continuous conversations;
- understand a request received through text or an approved voice path;
- select the smallest suitable existing NOVA capability;
- coordinate bounded specialist work only when that work is justified;
- track long-running work and report meaningful progress;
- ask a follow-up question only when a material decision is missing;
- return results in NOVA's normal conversational voice; and
- notify the owner when approved background work completes, once a separately
  reviewed notification path exists.

The owner should not need to know which internal component performed a task.
The owner must still be able to inspect what NOVA understood, what capability
it used, what evidence it relied on, what changed, and how to stop or recover
from an action.

## Architecture direction

```text
Owner
  |
  | voice or text
  v
NOVA Conductor
  |
  | intent, permission, and capability routing
  v
Existing NOVA domain services
  |-- Chat
  |-- Focus
  |-- Knowledge
  |-- Librarian
  |-- Intake
  |-- Project Record
  `-- future bounded capabilities
  |
  | optional specialist workers when evidence justifies them
  v
Result, progress, evidence, and audit history
  |
  v
NOVA Conductor
  |
  v
Owner
```

The first implementation should remain inside the modular monolith. A new
agent framework, message broker, service split, or orchestration platform is
not justified merely by approving this direction.

## Authority and safety boundaries

1. Existing domain services remain authoritative for their own data and
   actions. The Conductor routes requests; it does not bypass them.
2. Every material state change keeps its existing local-intent, approval,
   validation, audit, and recovery requirements.
3. Internal delegation never implies permission. A specialist receives only
   the minimum context and capability required for the approved task.
4. Conversation context is not permanent knowledge. Persistence continues
   through NOVA's explicit knowledge review workflow.
5. Specialists may be invisible as personalities, but their work is not
   invisible as evidence. NOVA must explain material recommendations and
   actions without exposing private reasoning traces.
6. The owner can stop running work. Failed or interrupted work must report a
   truthful state and must not invent a successful result.
7. Voice and typing may share one backend request model, but voice capture,
   transcription, retention, and notification delivery each require their own
   privacy and engineering review before implementation.
8. External models and software remain tools. They do not own NOVA's workflow,
   permissions, memory, or user relationship.

## Reuse decision

Future Conductor work must evaluate proven free and open-source routing,
workflow, and job-control components before custom implementation. Adoption is
not automatic: a dependency must improve reliability or reduce total
maintenance while preserving local operation, privacy, recovery, and NOVA's
authority boundaries.

The default first step is a small NOVA-owned integration over existing services.
Specialist agents are added only when measured work cannot be handled clearly
by a deterministic service or one bounded model call.

## Phased adoption

### Phase 1 - Unified capability routing

- Keep Chat as the visible conversational surface.
- Publish a bounded capability registry for existing NOVA services.
- Route only explicit, well-understood requests.
- Preserve current approval screens and guarded actions.
- Add no multi-agent runtime.

### Phase 2 - Trackable work

- Add a local job record only for genuinely long-running work.
- Report queued, running, waiting-for-owner, completed, failed, and cancelled
  states truthfully.
- Keep progress and results recoverable across a restart where required.
- Review notifications separately before enabling proactive delivery.

### Phase 3 - Bounded specialists

- Introduce one specialist only for a measured use case with a written
  contract, context limit, tool allowlist, timeout, and acceptance tests.
- Keep specialists behind the Conductor rather than adding separate user
  personalities or inboxes.
- Require the same approval and audit boundaries as direct NOVA actions.

### Phase 4 - Voice and broader clients

- Feed approved voice transcription into the same Conductor request path as
  typing.
- Evaluate a Progressive Web App before maintaining separate native clients.
- Add a native client only if measured platform limitations justify it.

## Explicit non-goals of this decision

This direction does not currently add:

- an agent framework or autonomous agent team;
- automatic task delegation from ordinary conversation;
- tools, plugins, web access, email, calendar, smart-home, or coding authority;
- background execution or proactive notifications;
- voice recording or transcription;
- a second memory, task, knowledge, or audit store; or
- permission to upload or share owner data.

Each capability still requires a bounded proposal, architecture review,
engineering review, explicit owner approval, implementation evidence, and
acceptance.

## Core principle

> The Conductor talks.
>
> Specialists perform bounded work.
>
> NOVA explains its actions.
>
> The owner remains in control.
