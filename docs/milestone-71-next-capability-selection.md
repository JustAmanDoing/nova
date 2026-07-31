# Milestone 71 - Evidence-Led Next Capability Selection

**Completion date:** 1 August 2026

**Base release:** 0.70.0

**Decision:** Complete; Milestone 72 Conversation Organisation selected,
runtime implementation not yet approved

## Objective

Choose one bounded capability after accepted phone daily-use validation. The
selection must improve NOVA as the owner's go-to system without weakening
local-first privacy, owner control, recoverability, AI optionality, or the
modular-monolith architecture.

## Evidence used

- Release 0.70.0 is installed, healthy, privately accessible, and accepted on
  the owner's phone.
- The owner explicitly prioritised a more intuitive and user-friendly daily
  experience.
- NOVA currently has 14 local conversations, and the new phone picker proves
  that changing conversations is a frequent navigation concern.
- The current chat contract supports create, list, open, and send, but exposes
  no owner rename, archive, restore, or deletion operation.
- The existing service already assigns a bounded title after a first message,
  but the owner cannot correct or organise that title later.
- Knowledge contains eight verified active records. Core coverage is 63.3
  percent, freshness is 100 percent, and eight of eight retrieval checks pass.
- Three core knowledge areas remain missing, but the accepted **Add through
  chat**, review, approval, revision, and retrieval workflow already addresses
  them without another runtime feature.
- Focus contains one verified project, one verified goal, and one completed
  next action. There is no open next action at the measurement time.
- Seven explicitly selectable local documents are available to Chat. Current
  evidence does not show a failure that requires implicit or semantic access.
- The runtime reports healthy with no warnings and more than 96 percent free
  N-drive storage.
- GitHub has no open NOVA issue requiring an urgent corrective release.

No personal record content, conversation text, document name, or action title
is copied into this decision document.

## Impact-first selection method

Candidates are scored from 1 to 5. Owner impact and direct evidence of an
unmet need contribute 60 percent of the weighted result:

- practical owner impact: 40 percent;
- evidence of a current unmet need: 20 percent;
- fit with the existing architecture: 15 percent;
- privacy and safety: 10 percent;
- reuse of verified NOVA components: 10 percent; and
- delivery and maintenance simplicity: 5 percent.

The score is a transparent comparison aid, not a claim of mathematical
certainty.

| Rank | Candidate | Impact | Evidence | Fit | Safety | Reuse | Delivery | Weighted |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Conversation rename, archive, and restore | 4 | 5 | 5 | 5 | 5 | 4 | 4.55 |
| 2 | Guided completion of remaining core knowledge | 3 | 5 | 5 | 5 | 5 | 5 | 4.20 |
| 3 | Broader filed-document workspace | 4 | 4 | 4 | 4 | 5 | 4 | 4.10 |
| 4 | Dates and reminders for owner-entered actions | 5 | 3 | 3 | 3 | 3 | 2 | 3.75 |
| 5 | Broad semantic document search | 5 | 3 | 3 | 3 | 2 | 2 | 3.65 |
| 6 | Voice conversation | 4 | 3 | 2 | 2 | 2 | 2 | 3.00 |
| 7 | User-controlled filing automation | 4 | 2 | 3 | 1 | 3 | 2 | 2.95 |

## Selected product slice

**Milestone 72 - Conversation Organisation**

Add an explicit, local conversation lifecycle. The owner can rename an active
conversation, archive it without deleting any message, view archived
conversations deliberately, and restore one to active use. Every change is
guarded, recorded, reversible, and independent of the model.

Archived conversations leave the default active picker but remain available in
an Archived view. An archived conversation is read-only until restored. The
first slice does not delete conversation data or search message content.

## Why this is the most impactful next step

- Fourteen conversations already create a measured organisation need.
- The owner has just accepted the phone picker and wants NOVA to become the
  easiest daily system to use.
- Rename and archive prevent the picker from becoming a growing undifferentiated
  list.
- Archive is reversible and safer than adding deletion.
- The change stays inside the existing chat module and local SQLite database.
- Existing local-intent guards, migration tooling, backup and restore,
  timestamp handling, responsive UI, and protected verification can be reused.
- The capability remains useful when Ollama is unavailable.
- No new provider, service, microphone, notification channel, account, vector
  database, or autonomous process is required.

## Why the other candidates are later

### Guided completion of core knowledge

The need is real, but NOVA already exposes the highest-value missing areas and
provides the accepted **Add through chat** workflow. The owner can improve
coverage now without waiting for engineering or creating another writing path.

### Broader filed-document workspace

Seven documents are already available through explicit selection, and Intake
already owns deterministic filing and search. More daily-use evidence should
identify the precise missing document journey before another interface is
added.

### Dates and reminders

Dates and reminders offer high value, but the owner currently has no open next
action and work-schedule knowledge is missing. Reliable time-zone handling,
delivery, missed reminders, notification permissions, and phone behavior need
a separate risk decision after owner-controlled action use grows.

### Semantic document search

Implicit retrieval would broaden document access and add embedding selection,
chunking, index lifecycle, deletion propagation, and retrieval-quality
requirements. Existing explicit context has no recorded failure requiring that
expansion.

### Voice

The owner has expressed interest, and private phone access now removes one
dependency. Voice still introduces microphone permission, speech retention,
local recognition and synthesis, interruption, accessibility, and mobile
battery decisions. It should follow a tidier long-lived conversation lifecycle.

### Filing automation

The existing recommend, approve, and execute separation remains an intentional
safety boundary. Current evidence does not justify reducing it.

## Decision boundary

Milestone 71 authorises selection, proposal, and review only. It does not
authorise a database migration, API change, frontend change, runtime rebuild,
version bump, release, automatic conversation action, or data deletion.

Milestone 72 runtime implementation requires the owner's explicit approval of
`docs/milestone-72-conversation-organisation-proposal.md`.

## Completion estimate

- Accepted practical local NOVA prototype: 100 percent.
- Broader long-term NOVA vision: approximately 86 percent.
- Milestone 71 decision work: 100 percent.

The broader estimate is unchanged because selection work does not add runtime
capability.

## Exact next action

Obtain explicit owner approval for Milestone 72. If approved, implement only
the bounded conversation rename, archive, restore, and lifecycle-audit slice;
then run protected verification, Windows runtime acceptance, phone acceptance,
and a release decision before selecting another capability.
