# Milestone 80 - Conductor Phase 1 Review Packet

**Decision date:** 9 August 2026

**Evidence base:** protected `main` at
`1905e442699d923c2ea6a70b62e17712684f330b`, completed Milestone 79 evidence,
the roadmap, architecture, development playbook, and approved Conductor north
star

**Status:** capability, reuse, architecture, engineering, risk, test, and
rollout reviews approved together by the owner for bounded implementation;
merge, release, installation, and physical acceptance are not approved

## Plain-language decision

Milestone 80 should make Chat the first small Conductor surface. Four clearly
listed requests can read information NOVA already owns and return a short
answer with visible evidence. They work without Ollama because no model is
needed to copy and format current local facts.

This is routing, not autonomy. The Conductor cannot edit a project, complete an
action, change knowledge, file a document, browse the web, start background
work, or choose a hidden tool. Existing services remain in charge of their own
data and actions.

## Evidence-led capability discussion

The three strongest candidates were compared against the accepted installed
NOVA 0.78.2 behavior.

| Candidate | Owner value | Reuse | Privacy | Complexity | Maintenance |
| --- | --- | --- | --- | --- | --- |
| **Conductor Phase 1: four read-only status requests in Chat** | High: one familiar surface can answer what is next, what is active, what needs review, and what NOVA version evidence says | Very high: reuses Chat, Focus, Next actions, Knowledge, Librarian, Project Record, SQLite, and private phone access | Strong: local reads only; no new provider, upload, or document exposure | Low to moderate: a small registry, exact routing, response formatting, evidence persistence, and UI starters | Low: four explicit contracts owned inside the modular monolith |
| **Librarian suggestion dismissal** | Medium: removes repeated optional suggestions the owner does not want | High: reuses Librarian and knowledge review UI | Strong, but adds a new preference about what to suppress | Moderate: requires durable dismissal state, reset behavior, audit meaning, and rules for changed evidence | Moderate: every future suggestion type must define dismissal semantics |
| **Dates and reminders Phase 1** | High: useful in daily life | Medium: can reuse Focus and Windows, but NOVA has no time or notification authority yet | Mixed: schedules and notification contents create additional sensitive state | High: time zones, recurrence, delivery, missed events, restart recovery, and phone behavior | High: OS and notification integrations require ongoing compatibility work |

### Recommendation

Choose Conductor Phase 1. It is the clearest next step in the already approved
interaction direction, gives visible value on PC and phone, and proves routing
and evidence without granting write or background authority. Librarian
dismissal remains a useful later usability candidate. Dates and reminders
should wait for a separate measured need and dedicated privacy, delivery, and
recovery review.

No third-party framework is justified. A new agent SDK, workflow engine,
message broker, vector database, or cloud model would increase privacy and
maintenance cost without improving these four deterministic reads.

## Architecture Review

This proposal was presented in plain language as unapproved. The owner then
approved it as part of the combined milestone packet on 9 August 2026.

### What the owner sees

Chat lists four **Ask NOVA locally** starters:

- Show my open next actions.
- Show my projects and goals.
- What needs review in Librarian?
- Show NOVA project status.

Choosing one prepares its exact text. Sending it returns at most five items per
section, says where the answer came from, shows when that source was checked,
and stores a hash of the returned answer with the chat message. The source card
links to the existing owning page for the full record.

### Ownership and flow

```text
Owner in Chat
  -> exact request matched in the published capability registry
  -> small Conductor service
       -> existing Next actions service
       -> existing Knowledge planning projection
       -> existing read-only Librarian
       -> existing Project Record
  -> short result plus source, time, and result hash
  -> existing local chat history
```

The owning service remains the source of truth. The Conductor creates no
second project, task, knowledge, or project-record store.

### Trust and privacy boundaries

- Routing is an exact normalized match against published phrases. There is no
  fuzzy classifier, model-selected tool, prompt interpretation, or hidden
  delegation.
- All reads stay inside the existing local FastAPI process and configured local
  storage. No new network request or provider is introduced.
- Source links are fixed NOVA routes, never source-supplied destinations.
- The response is bounded before it reaches Chat.
- Chat history stores the result and evidence metadata. It does not copy the
  underlying project, action, knowledge, or archive source into a new domain
  store.
- A Conductor request has no write authority over any owning service. The
  existing browser-intent guard still protects the chat submission itself.

### Failure and recovery

If an owning read fails, Chat reports that NOVA could not read the capability
and that no domain data was changed. As with a failed model reply, the submitted
user message may remain in local conversation history, but no invented
assistant result or capability evidence is saved.

Migration 18 is additive. It creates only the assistant-message evidence table
and does not rewrite existing messages. Existing verified database backup and
restore controls cover it. Rolling the application code back leaves an older
runtime unable to accept the newer schema, so runtime rollback must restore the
verified pre-update database backup through the existing guarded process.

### Explicit non-goals

Milestone 80 does not add natural-language intent inference, multi-agent work,
specialists, tools, writes through Chat, automatic actions, background jobs,
notifications, voice, web access, external models, or a new approval path.

## Engineering Review

### Bounded implementation

- Add one static capability registry and one `ConductorService` inside the
  existing backend modular monolith.
- Publish the registry at `GET /api/v1/chat/capabilities`.
- Let the existing message endpoint accept no model only when an exact listed
  capability matches and no document is selected.
- Persist source title, fixed local URL, generation time, capability ID, and
  response SHA-256 against the completed assistant message in Migration 18.
- Add starter buttons and evidence cards to the existing Chat page. Keep a
  model mandatory for ordinary chat and selected-document turns.
- Add no runtime dependency.

### Required proof

- The registry exposes exactly the four reviewed capabilities.
- Every handler reads its existing owner service, returns bounded truthful
  output, and never calls the model.
- A recognized request succeeds when Ollama is unavailable.
- An unrecognized request without a model fails before writing chat history.
- Capability evidence survives conversation reload and database migration.
- Existing model chat, knowledge retrieval, document selection, lifecycle,
  Focus, Librarian, Project Record, intake, backup, and restore tests regress
  cleanly.
- Backend Ruff, strict mypy, full pytest with coverage, frontend lint,
  typecheck, tests, build, repository whitespace checks, Windows controller
  checks, Compose validation, and protected GitHub CI pass where the current
  environment provides them.

### Rollout and acceptance

Implementation may proceed on a feature branch and be published as a draft
pull request. Merge requires the owner's later approval after final diff,
independent review, and protected CI evidence. Release and guarded Windows
installation remain separate. Physical PC and private-phone acceptance must
confirm all four starters, offline behavior, evidence links, and no unexpected
domain change before Milestone 80 can be called complete.

Any request to add a fifth capability, write action, model-based router,
dependency, external provider, background work, or network change is a material
scope change and returns to review.

## Candidate verification

The feature-branch candidate completed a distinct final scope, privacy,
failure, migration, recovery, and regression review after implementation. The
review removed unlisted route synonyms so only the four published phrases can
select a capability, added safe local-link and SHA-256 response validation, and
added a truthful failure-path test.

- Backend Ruff: passed.
- Backend strict mypy: passed for 42 source files.
- Backend pytest: 169 passed with 93.56% coverage.
- Frontend lint and typecheck: passed.
- Frontend Vitest: 58 passed. The existing non-failing React `act(...)`
  warnings remain outside this milestone.
- Frontend production build: passed.
- CI/workflow, container-contract, container-policy, and repository-hygiene
  static tests: 10 passed.
- Working-tree whitespace check: passed.
- PowerShell Windows-control and local Docker/Compose execution: not available
  in the Remote sandbox; the unchanged Windows controls and the new isolated
  no-model Conductor smoke path remain required in protected GitHub CI.

This is candidate evidence only. It does not represent protected CI, merge,
release, installation, or owner acceptance.
