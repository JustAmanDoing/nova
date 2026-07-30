# Milestone 64 - Evidence-Led Next Capability Selection

**Completion date:** 30 July 2026

**Base release:** 0.63.0

**Decision:** Complete; Milestone 65 Active Projects and Goals Workspace
selected, runtime implementation not yet approved

## Objective

Choose the next bounded capability in order of owner impact while preserving
NOVA's local-first privacy, owner control, recoverability, and modular-monolith
architecture.

## Evidence used

- Milestone 63 is installed and accepted on release 0.63.0.
- The local runtime is healthy and all protected checks pass.
- The knowledge-health report identifies both **Active projects** and
  **Current goals** as missing five-star core areas.
- The four active approved records currently contain facts and references, but
  no active project or goal record.
- NOVA already supports owner-approved `project` and `goal` knowledge types,
  immutable revisions, retirement, checksum verification, snapshots,
  retrieval, and guided add-through-chat prompts.
- The current chat page mixes conversation, memory review, knowledge health,
  and the complete knowledge library; a focused planning view does not exist.
- Milestone 63 proved that a narrow bridge between existing modules can add
  practical value without introducing a new service or external provider.

No personal record content was copied into this decision document.

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
| 1 | Active projects and goals workspace | 5 | 5 | 5 | 5 | 5 | 4 | 4.95 |
| 2 | Explicit filed-library document context | 5 | 4 | 5 | 4 | 5 | 4 | 4.65 |
| 3 | Broad semantic document search | 5 | 3 | 3 | 3 | 2 | 2 | 3.65 |
| 4 | Secure phone access to NOVA | 5 | 3 | 2 | 2 | 3 | 2 | 3.50 |
| 5 | User-controlled filing automation | 4 | 2 | 3 | 1 | 3 | 2 | 2.95 |
| 6 | Voice conversation | 4 | 2 | 2 | 2 | 2 | 2 | 2.80 |

## Selected product slice

**Milestone 65 - Active Projects and Goals Workspace**

Add a local, read-only-first focus board that shows current owner-approved
`project` and `goal` records in separate sections. It reuses the existing
knowledge lifecycle and guided chat capture rather than creating a second
planning database.

The owner can:

1. see verified active projects and goals without searching conversation
   history;
2. see when each item was last updated and whether review is due;
3. use the existing guided chat flow to add a missing project or goal;
4. open the existing knowledge controls to correct or retire an item; and
5. understand that NOVA is displaying approved facts, not inventing progress
   or priorities.

## Why this is the most impactful next step

- It addresses the two highest-priority gaps measured by NOVA itself.
- Projects and goals are central to the owner's stated chief-of-staff vision.
- It turns approved memory into a daily-use planning surface.
- It remains useful when Ollama is unavailable because the overview is
  deterministic and read-only.
- It needs no external service, vector database, new AI provider, task engine,
  or autonomous planner.
- It exercises existing knowledge capture, quality, revision, retirement,
  backup, and retrieval controls instead of duplicating them.

## Why the other candidates are later

### Explicit filed-library document context

This is the next strongest document capability and should remain near the top
of the queue. The current evidence shows that projects and goals are missing
core knowledge, while explicit intake-document context is already working.

### Broad semantic document search

The owner value is high, but automatic retrieval would expand implicit access
and introduce embedding-model, vector-index, chunking, lifecycle, and
retrieval-quality decisions. Explicit selection remains the safer evidence
path.

### Secure phone access

Phone access is highly useful, but the NOVA application is deliberately
loopback-only. Authentication, private transport, sessions, origins, recovery,
and the remote threat model require their own product and security decision.

### User-controlled filing automation

The current approve-then-execute separation is an intentional safety boundary.
Observed recommendation accuracy and owner-defined rules do not yet justify
reducing that friction.

### Voice conversation

Voice adds microphone permissions, local speech recognition and synthesis,
interruption, retention, and mobile-access dependencies. It should follow a
stable daily planning experience and an explicit access decision.

## Decision boundary

Milestone 64 authorizes selection and proposal review only. It does not
authorize a database migration, API change, frontend change, runtime rebuild,
version bump, or release.

Milestone 65 runtime implementation requires explicit owner approval of
`docs/milestone-65-active-projects-goals-workspace-proposal.md`.

## Completion estimate

- Milestone 64 decision work: 100%.
- Accepted practical local prototype: 100%.
- Broader long-term NOVA vision: approximately 79%.

## Exact next action

Obtain explicit owner approval for Milestone 65. If approved, implement only
the bounded active-projects-and-goals workspace, verify it through the protected
workflow and Windows acceptance, and issue a release decision before selecting
another capability.
