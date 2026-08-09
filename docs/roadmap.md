# Nova Roadmap

## Foundation — complete

- FastAPI and React monorepo
- Typed, versioned API and health checks
- Docker Compose local environment
- Backend and frontend tests
- Reproducible Node 20 and pnpm 9.15.5 build
- Structured extraction diagnostics
- Filename, extracted-text, evidence, and metadata/status search
- Resilient background scanning and per-file parser isolation
- Stale inventory reconciliation and stable unfiltered dashboard totals
- Independent source-file and expanded-text safety limits
- Ordered, recorded, transactional SQLite schema migrations
- Double-click Windows start, stop, status, and guarded update controls
- Automatic backend, frontend, Windows-control, and production-container checks
- Browser-integrity guard on every state-changing local API request
- Read-only storage, database-size, and intake-scan health measurements
- Isolated production startup, dashboard, API, and intake smoke verification
- Local Host validation and restrictive dashboard browser security headers
- Portable bind-mount initialization with an immediate application privilege drop
- Keyboard-visible focus, live status announcements, and accessible intake table context
- Startup rejection of overlapping intake, library, backup, and database paths
- Non-overlapping dashboard refresh that pauses while the page is hidden
- Current supported Starlette `httpx2` test transport without deprecation warnings
- Cross-platform Python dependency constraints used by CI and production builds
- Automatic bounded container diagnostics after a failed Windows startup
- Read-only active-database integrity verification before migrations
- Explicit `no-store` policy for every API response
- Dashboard entry-page revalidation after application updates
- Patched pytest and Vitest toolchains with an advisory-clean resolved lock set
- Immutable commit pinning for every external GitHub Actions dependency
- Isolated production verification of approval, move, audit, undo, backup, and
  restore boundaries
- Git-enforced Linux entrypoint line endings with Windows-runner verification
- Runtime detection of source and container version drift on Windows
- Verified online database snapshot before a running Windows deployment updates
- Explicit loopback readiness probes with a diagnostic three-minute startup window
- Public-repository ignore rules, private vulnerability reporting, and tracked-file checks
- Immutable verified digests for all production container base images
- Representative production acceptance across TXT, Markdown, DOCX, PDF, image
  OCR, search, learning refresh, move, undo, backup, and restore
- Early storage capacity guidance in the dashboard and Windows status controls
- Checksum- and integrity-verified backup downloads for independent recovery copies
- Accessible full backup history with the newest five shown by default
- Read-only retained-backup count, storage use, and checksum-record summary
- Minute-bounded automatic backup inventory refresh with immediate manual refresh
- Latest-request-wins dashboard state during overlapping manual and background loads
- Precise backup-history wording that distinguishes a recorded checksum from
  full download or restore verification
- Prompt retry after a failed automatic backup-history refresh
- Core dashboard updates remain available when optional backup history fails
- Independent dashboard resource refresh with scoped partial-failure diagnostics
- Filename-bound checksum sidecars for portable backup integrity
- Distinct current-verification and checksum-recorded backup API states
- Backup inventory remains available when one discovered snapshot disappears
- One-click, read-only active-database integrity verification

## Milestone 1 — Observe — complete

- Read-only local intake folder
- Background and manual scanning
- File metadata and SHA-256 fingerprinting
- Exact-duplicate detection
- Local SQLite inventory
- Intake dashboard

## Milestone 2 — Understand — complete

- Extract text from TXT and Markdown — complete
- Store normalized title, preview, counts, status, and evidence — complete
- Show understanding results in the dashboard — complete
- Enforce a configurable local extraction size limit — complete
- Add PDF and DOCX extraction — complete
- Keep understanding and recommendation processing local and read-only — complete
- Add local OCR for scanned PDFs and images — complete

## Milestone 3 — Recommend — complete

- Deterministic rules before AI — complete
- Suggest a category, approved-format filename, and destination — complete
- Include confidence and a plain-language explanation — complete
- Return no recommendation when evidence is insufficient — complete
- Recalculate after source, understanding, duplicate-status, or rule-version changes — complete
- Keep all recommendations read-only with no filesystem action controls — complete

## Milestone 4 — Approve, execute, and audit — complete

- Approval queue with approve, edit, reject, ignore, and review-again actions — complete
- Persist review state against the exact recommendation version — complete
- Return changed recommendations to the queue — complete
- Validate edited filename and destination values — complete
- Keep approval separate from execution — complete
- Move into the library only after current approval and separate confirmation — complete
- Refuse overwrite, changed sources, stale approvals, and unsafe paths — complete
- Reverify SHA-256 immediately before source removal — complete
- Append-only operation event audit — complete
- Reversible execution and guarded undo — complete

## Operational hardening — recovery diagnostics — complete

- Detect operations left in `started` state beyond a safety delay — complete
- Reinspect source and destination paths without changing them — complete
- Compare current files with the recorded SHA-256 — complete
- Distinguish safe retry, likely completion, duplicate copy, conflict, missing,
  unsafe-path, and unreadable outcomes — complete
- Surface clear manual-review guidance in the dashboard — complete
- Keep all recovery assessment read-only — complete
- Create consistent, integrity-checked database backups — complete
- Store backups outside the Docker database volume — complete
- Bind the local deployment to the loopback interface — complete
- Add an explicit verified restore workflow — complete

## Milestone 5 — Learn and advanced search

- Learn preferred destinations only from successful confirmed moves — complete
- Invalidate a learning example when its move is undone — complete
- Keep learned suggestions behind explicit approval and execution — complete
- Inspect and explicitly forget stored learning groups — complete
- Deterministic multi-term and phrase-aware ranked search — complete
- Semantic search
- User-controlled automation rules
- Measured thresholds before any automatic filing

## Milestone 53 — Local v1 completion review

**Status (28 July 2026): complete; local v1 accepted.**

- Static usability and accessibility defects corrected and verified
- Architecture and scope boundaries reconfirmed
- Full automated verification matrix passed
- Docker production workflow passed
- Representative Windows-host and browser acceptance passed

The detailed evidence and open blockers are recorded in
`docs/milestone-53-local-v1-completion-review.md`.

## Milestone 54 — Local Chat Core

**Status (28 July 2026): complete; working local prototype accepted.**

- Local Ollama model discovery and streaming chat — complete
- Local conversation history — complete
- Stop generation — complete
- Clear provider-failure handling — complete
- No tools, web access, RAG, or permanent personal-memory promotion — preserved

The evidence and current limitations are recorded in
`docs/milestone-54-local-chat-core.md`.

## Milestone 55 — Conversation-to-Knowledge Capture

**Status (28 July 2026): complete; engineering and owner acceptance passed.**

- Natural explicit "remember this" requests — complete
- Limited deterministic suggestions for high-value candidate knowledge —
  complete
- Editable owner review before any permanent personal record is created —
  complete
- Approval writes a local, no-overwrite Markdown record and recoverable SQLite
  record — complete
- Rejection creates no permanent record — complete
- No silent memory promotion — verified

The evidence and limitations are recorded in
`docs/milestone-55-conversation-to-knowledge-capture.md`.

## Milestone 56 — Approved Knowledge Retrieval

**Status (28 July 2026): complete; engineering and owner acceptance passed.**

- Retrieve only owner-approved knowledge records — complete
- Verify the current local record path and SHA-256 before retrieval — complete
- Cite the exact local record used in an answer — complete
- Persist citation evidence with the assistant message — complete
- Keep retrieval separate from general model training and chat history —
  complete
- Provide clear no-match and retrieval-failure behavior — complete
- Preserve local-only operation and owner control — complete

The evidence and limitations are recorded in
`docs/milestone-56-approved-knowledge-retrieval.md`.

## Milestone 57 — Knowledge Lifecycle and Duplicate Controls

**Status (29 July 2026): complete; architecture, engineering, and owner
acceptance passed.**

- Flag deterministic likely duplicates before approval — implemented
- Require explicit confirmation to preserve likely duplicates separately —
  implemented
- Update approved records through immutable, no-overwrite revisions —
  implemented
- Retire records from retrieval without deleting files or history — implemented
- Preserve append-only lifecycle events and revision metadata — implemented
- Create checksum-verified snapshots of all tracked Markdown revisions —
  implemented
- Preserve approved-only retrieval and all local safety boundaries — verified

The evidence and current decision are recorded in
`docs/milestone-57-knowledge-lifecycle.md`.

## Milestone 58 — Knowledge Quality and Gap Analysis

**Status (29 July 2026): complete; architecture, engineering, and owner
acceptance passed.**

- Verify every active record before including it in quality reporting —
  implemented
- Measure priority-weighted core capability coverage against a published
  seven-item checklist — implemented
- Track review-age freshness without treating stale information as missing —
  implemented
- Keep optional opportunities outside the core completion score — implemented
- Rank missing and review-due suggestions without changing knowledge —
  implemented
- Run a bounded deterministic retrieval self-check over active records —
  implemented
- Isolate quality-report failures so chat and knowledge remain usable —
  verified
- Preserve local-only operation, explicit approval, and non-destructive
  lifecycle controls — verified

The method, evidence, and current decision are recorded in
`docs/milestone-58-knowledge-quality-gap-analysis.md`.

## Milestone 59 — Guided Knowledge Onboarding

**Status (29 July 2026): complete; architecture, engineering, Windows, and
owner acceptance passed.**

- Turn a selected missing area into one focused, editable chat prompt —
  implemented
- Never send a prompt or save knowledge from a suggestion click alone —
  verified
- Reuse the existing conversation, proposal, and approval workflow —
  implemented
- Let review-due suggestions identify the matching approved record —
  implemented
- Refresh Knowledge health after an approved update — preserved
- Keep optional areas visibly optional — verified
- Preserve all local-only, owner-approval, and no-silent-memory boundaries —
  verified

The implementation and evidence are recorded in
`docs/milestone-59-guided-knowledge-onboarding.md`.

## Milestone 60 — Repository Integration and Protected Main

**Status (29 July 2026): complete; release 0.59.0 published from protected
`main`.**

- Repository integration was bound to one exact pull-request head and its
  successful checks — complete
- Backend, frontend, Windows, and production-runtime checks are required on
  protected `main` — complete
- Force pushes and deletion are disabled without locking out the sole owner —
  complete
- Milestones 53–59 remain individual commits behind one merge commit —
  complete
- N-drive working copy and installed runtime were aligned with verified
  `main` — complete
- Annotated tag `v0.59.0` and GitHub release `Release 0.59.0` were published
  after post-merge verification — complete

The final outcome and review evidence are recorded in:

- `docs/milestone-60-repository-integration-proposal.md`
- `docs/milestone-60-architecture-review.md`
- `docs/milestone-60-engineering-review.md`
- `docs/milestone-60-release-report.md`

## Milestone 61 — Daily-Use Beta Validation

**Status (30 July 2026): complete; release 0.59.0 remained stable and owner
acceptance passed.**

- Real local conversation and knowledge activity observed without publishing
  personal content — complete
- Container stability and logs reviewed — complete
- Active database and approved knowledge verified — complete
- Fresh database and knowledge recovery checkpoints verified — complete
- Backend, frontend, Windows, Compose, and runtime boundary checks repeated —
  complete
- No release-blocking defect found — complete

The evidence and decisions are recorded in:

- `docs/milestone-61-daily-use-beta-validation.md`
- `docs/milestone-61-architecture-review.md`
- `docs/milestone-61-engineering-review.md`

## Milestone 62 — Evidence-Led Next Capability Selection

**Status (30 July 2026): complete; explicit local document context selected.**

- Beta evidence and current owner priorities reviewed — complete
- Six bounded candidates ranked by value, architecture fit, privacy, reuse,
  delivery, and maintenance — complete
- Milestone 63 explicit local document context selected — complete
- Architecture and engineering proposal reviews passed — complete
- Runtime implementation remains gated by explicit owner approval — preserved

The selection and reviews are recorded in:

- `docs/milestone-62-next-capability-selection.md`
- `docs/milestone-62-architecture-review.md`
- `docs/milestone-62-engineering-review.md`
- `docs/milestone-63-explicit-document-context-proposal.md`

## Milestone 63 — Explicit Local Document Context

**Status (30 July 2026): complete; release 0.63.0 integrated, installed, and
accepted on the Windows host.**

- Let the owner explicitly select one ready intake document for one chat turn
- Revalidate current source path and SHA-256 before use
- Add at most 8,000 UTF-8 bytes as untrusted local `[D1]` context
- Persist citation metadata only for completed assistant responses
- Keep full extracted text out of browser API responses
- Preserve no-selection behavior and every existing safety boundary
- Exclude semantic search, automatic retrieval, uploads, broad host access,
  tools, voice, remote access, plugins, agents, and automation
- Backend, frontend, migration, privacy, stale-source, and no-selection
  regression tests pass
- Architecture and engineering completion reviews pass

Completion evidence is recorded in:

- `docs/milestone-63-architecture-review.md`
- `docs/milestone-63-engineering-review.md`
- `docs/milestone-63-release-report.md`

## Milestone 64 — Evidence-Led Next Capability Selection

**Status (30 July 2026): complete; Active Projects and Goals Workspace
selected and subsequently approved by the owner.**

- Milestone 63 evidence and current knowledge gaps reviewed — complete
- Candidates ranked with owner impact and direct evidence weighted highest —
  complete
- Milestone 65 Active Projects and Goals Workspace selected — complete
- Architecture and engineering proposal reviews passed — complete
- Runtime implementation remained gated until explicit owner approval —
  complete

The selection and reviews are recorded in:

- `docs/milestone-64-next-capability-selection.md`
- `docs/milestone-64-architecture-review.md`
- `docs/milestone-64-engineering-review.md`
- `docs/milestone-65-active-projects-goals-workspace-proposal.md`

## Milestone 65 — Active Projects and Goals Workspace

**Status (30 July 2026): complete; release 0.65.0 integrated, installed, and
accepted on the Windows host.**

- Show verified active project and goal knowledge in a focused local view
- Reuse guided chat capture and the existing immutable knowledge lifecycle
- Show freshness without inventing progress, priority, dates, or next actions
- Keep the first slice read-only-first and useful without Ollama
- Exclude tasks, calendars, reminders, automation, semantic retrieval, voice,
  remote access, plugins, agents, tools, web access, and external providers
- Protected PR #7 and post-merge `main` passed the complete verification
  matrix
- Installed Windows release, Focus browser workflow, backup, database
  integrity, privacy boundaries, and responsive layout passed

Implementation and review evidence:

- `docs/milestone-65-active-projects-goals-workspace-proposal.md`
- `docs/milestone-65-implementation.md`
- `docs/milestone-65-architecture-review.md`
- `docs/milestone-65-engineering-review.md`
- `docs/milestone-65-acceptance.md`
- `docs/milestone-65-release-report.md`

## Milestone 66 — Focus Workspace Daily-Use Validation

**Status (31 July 2026): complete; genuine owner-approved records, immutable
correction behavior, integrity filtering, and owner usefulness were
validated.**

- One genuine active project and one genuine current goal added through the
  existing owner-review workflow — complete
- Both records displayed in the correct Focus sections with current review
  state — complete
- One approved correction created revision 2 while preserving revision 1 —
  complete
- Retirement not exercised because the owner had no genuine record to retire
- Owner usefulness, clarity, and non-intrusiveness acceptance — passed
- Runtime health, database integrity, knowledge integrity, and retrieval
  self-checks — passed

Completion evidence:

- `docs/milestone-66-focus-workspace-daily-use-validation.md`
- `docs/milestone-66-architecture-review.md`
- `docs/milestone-66-engineering-review.md`

## Milestone 67 — Evidence-Led Next Capability Selection

**Status (31 July 2026): complete; Owner-Approved Next Actions selected and
subsequently approved by the owner.**

- Milestone 66 evidence and the owner's current priorities reviewed — complete
- Candidates ranked by impact, urgency, privacy, complexity, reuse, and
  maintenance cost — complete
- Milestone 68 Owner-Approved Next Actions selected — complete
- Architecture and engineering proposal reviews — passed
- Runtime implementation remained gated until explicit owner approval —
  complete

Decision and proposal evidence:

- `docs/milestone-67-next-capability-selection.md`
- `docs/milestone-67-architecture-review.md`
- `docs/milestone-67-engineering-review.md`
- `docs/milestone-68-owner-approved-next-actions-proposal.md`

## Milestone 68 — Owner-Approved Next Actions

**Status (31 July 2026): complete; release 0.68.0 integrated, installed,
recovery-tested, and accepted by the owner.**

- Add one bounded local Next actions section to Focus
- Accept only explicit owner-entered actions
- Support open, complete, and reopen with append-only local history
- Allow an optional verified active-project association
- Exclude priorities, dates, reminders, recurrence, notifications, automatic
  extraction, model-generated plans, and autonomous execution
- Preserve local-first, privacy-first, AI-optional, recovery, and
  modular-monolith boundaries
- Protected PR #11 and post-merge `main` passed the complete verification
  matrix
- Installed Windows release, migration 16, backup and restore, database
  integrity, privacy controls, responsive layout, and genuine owner lifecycle
  passed

Implementation and review evidence:

- `docs/milestone-68-owner-approved-next-actions-proposal.md`
- `docs/milestone-68-implementation.md`
- `docs/milestone-68-architecture-review.md`
- `docs/milestone-68-engineering-review.md`
- `docs/milestone-68-acceptance.md`
- `docs/milestone-68-release-report.md`

## Milestone 69 - Secure Tailnet Phone Access

**Status (31 July 2026): complete; release 0.69.0 integrated, installed,
recovery-tested, and accepted.**

The owner reprioritized secure phone access as a prerequisite for the planned
daily-use validation.

- Reuse the owner's existing authenticated Tailscale network
- Keep frontend and backend Docker publications on Windows loopback
- Use private Tailscale Serve and explicitly prohibit public Funnel
- Route the browser interface and API through one same-origin HTTPS address
- Keep the backend Host allowlist and CORS policy local-only
- Accept only localhost and the exact configured Tailscale DNS Host at Nginx
- Provide guarded, auditable, reversible Windows controls
- Validate chat, Focus, knowledge, and one reversible guarded action on phone
- Keep the phone message composer within reach while chat scrolls, without
  covering the Knowledge panels
- Target release `0.69.0`

Proposal and review evidence:

- `docs/milestone-69-secure-phone-access-proposal.md`
- `docs/milestone-69-implementation.md`
- `docs/milestone-69-architecture-review.md`
- `docs/milestone-69-engineering-review.md`
- `docs/milestone-69-acceptance.md`

## Milestone 70 - Phone Daily-Use Validation

**Status (31 July 2026): complete; release 0.70.0 integrated, installed,
privately accessible, and accepted by the owner.**

The implementation merged through protected PR #15 and was rebuilt from exact
`main`. Automated, runtime, desktop, phone-sized browser, physical-phone owner,
and evidence-only protected release checks passed.

- Use the accepted phone route naturally rather than adding synthetic features
- Measure connection reliability, responsiveness, usability, and approval
  friction
- Exercise owner-approved next actions in genuine daily planning
- Record defects and owner feedback before selecting another capability
- Treat ease of use as a product requirement: keep important phone controls
  within reach, show one clear primary action, use consistent navigation,
  reduce technical wording, and place deeper details behind optional views
- Correct evidence-backed usability defects before adding another capability
- Preserve the accepted 0.69.0 runtime while evidence is collected

Evidence-backed candidate corrections:

- Keep the same three primary destinations visible in a sticky phone header
- Replace the sideways conversation history with one compact picker on phone
- Put owner-entered next actions before project and goal reference cards
- Make review links and primary navigation comfortable phone touch targets
- Keep essential wording visible while placing deeper technical explanations
  behind optional details
- Remove the Intake page's phone-width horizontal drift

Acceptance and review evidence:

- `docs/milestone-70-phone-daily-use-validation.md`
- `docs/milestone-70-architecture-review.md`
- `docs/milestone-70-engineering-review.md`
- `docs/milestone-70-release-report.md`

## Milestone 71 - Evidence-Led Next Capability Selection

**Status (1 August 2026): complete; Milestone 72 Conversation Organisation
selected and owner-approved.**

- Review measured daily-use evidence and current owner priorities
- Rank candidate improvements by impact, urgency, privacy, complexity, reuse,
  and maintenance cost
- Recommend one bounded next capability or recommend no runtime change
- Require architecture and engineering review before requesting runtime
  approval
- Do not start another runtime feature from this roadmap entry

Decision and proposal evidence:

- `docs/milestone-71-next-capability-selection.md`
- `docs/milestone-71-architecture-review.md`
- `docs/milestone-71-engineering-review.md`
- `docs/milestone-72-conversation-organisation-proposal.md`

## Milestone 72 - Conversation Organisation

**Status (1 August 2026): release approved; protected implementation merged,
exact merged runtime verified, and evidence-only integration and publication
remain.**

- Let the owner rename a local conversation explicitly
- Let the owner archive and restore a conversation without deleting messages
- Keep archived conversations outside the default active picker while making
  them deliberately reviewable
- Record created, renamed, archived, and restored lifecycle events locally
- Guard every mutation with the existing local-intent boundary
- Prevent sending into an archived conversation until the owner restores it
- Add no permanent deletion, automatic retention, AI-generated organisation,
  external sync, sharing, semantic search, or background action

Implementation and acceptance evidence:

- `docs/milestone-72-implementation.md`
- `docs/milestone-72-acceptance.md`
- `docs/milestone-72-release-report.md`

## Milestone 73 - Conversation Organisation Daily-Use Validation

**Status (3 August 2026): complete; daily use identified an inaccurate
capability-guidance defect and selected Milestone 74 as the bounded
correction.**

- Use normal phone and PC chat for several days.
- Record friction, failed recovery expectations, and conversation-list growth.
- Confirm Rename, Archive, Trash, Restore, latest-message navigation, and New
  chat remain understandable in daily use.
- Make no new runtime feature from this validation milestone.

Evidence:

- `docs/milestone-73-conversation-organisation-daily-use-validation.md`

## Milestone 74 - Accurate Capability Guidance

**Status (3 August 2026): product implementation merged and exact merged-main
runtime verified; evidence-only integration, tag, and publication remain.**

- Explain NOVA's verified local capabilities before limitations.
- Distinguish Chat context from guarded controls elsewhere in NOVA.
- Give product-specific, practical guidance instead of generic assistant
  boilerplate.
- Preserve memory approval, explicit document selection, local-only operation,
  and all existing action boundaries.
- Add no tool, web provider, external service, autonomous action, permission,
  or automatic data access.

Proposal and review evidence:

- `docs/milestone-74-capability-guidance-proposal.md`
- `docs/milestone-74-architecture-review.md`
- `docs/milestone-74-engineering-review.md`
- `docs/milestone-74-implementation.md`
- `docs/milestone-74-acceptance.md`
- `docs/milestone-74-release-report.md`

## Milestone 75 - Evidence-Led Next Capability Selection

**Status (3 August 2026): complete; Milestone 76 Local NOVA Project Record
selected and explicitly requested by the owner.**

- Review verified daily-use evidence, current owner priorities, and remaining
  low-priority limitations.
- Rank candidate improvements by impact, urgency, privacy, complexity, reuse,
  and maintenance cost.
- Recommend one bounded next capability or recommend no runtime change.
- Complete architecture and engineering review before requesting runtime
  approval.
- Do not start another runtime feature from this roadmap entry.

Decision and review evidence:

- `docs/milestone-75-next-capability-selection.md`
- `docs/milestone-75-architecture-review.md`
- `docs/milestone-75-engineering-review.md`

## Milestone 76 - Local NOVA Project Record

**Status (5 August 2026): complete; Releases 0.76.0, 0.76.1, and the accepted
0.76.2 knowledge-gap correction are published.**

- Maintain one canonical local current-status record.
- Catalogue authoritative repository evidence, verified runtime evidence,
  approved knowledge, dated local archives, and explicitly imported raw
  sources without replacing their ownership.
- Add a read-only Project record view for PC and private phone access.
- Add a guarded host-side import for one owner-selected NOVA-only source.
- Preserve originals, checksums, dates, and source labels with no overwrite.
- Keep raw chat exports outside Git and separate from approved knowledge.
- Do not access ChatGPT automatically, import unrelated chats, add semantic
  search, or promote raw content into knowledge automatically.

Proposal and review evidence:

- `docs/milestone-76-local-nova-project-record-proposal.md`
- `docs/milestone-75-architecture-review.md`
- `docs/milestone-75-engineering-review.md`

Implementation and acceptance evidence:

- `docs/milestone-76-implementation.md`
- `docs/milestone-76-acceptance.md`
- `docs/milestone-76-release-report.md`

## Milestone 77 - Local Project Record Daily-Use Validation

**Status (5 August 2026): complete. The owner accepted private-phone operation,
confirmed previously approved suggestions disappeared after the 0.76.2 fix,
and explicitly approved proceeding to Milestone 78. No synthetic import was
added merely to satisfy the optional validation scenario.**

- Use Record naturally on PC and phone after Release 0.76.0.
- Confirm the canonical project summary remains understandable and current.
- Import only owner-selected NOVA sources and verify the authority labels remain
  clear.
- Measure catalogue growth, preview usefulness, and import friction before
  selecting another capability.
- Make no new runtime feature from this validation milestone.

Validation evidence:

- `docs/milestone-77-local-project-record-daily-use-validation.md`
- `docs/milestone-77-knowledge-gap-correction.md`

## Milestone 78 - The Librarian

**Status (5 August 2026): complete. Release 0.78.1 is installed and the owner
accepted the read-only Librarian on both PC and private phone. Release 0.78.2
records the acceptance evidence and closes the milestone.**

- Provide a first-class read-only Knowledge Health page.
- Reuse the existing store, revisions, checksums, duplicate score, quality
  checklist, source confidence, and review workflow.
- Report deterministic duplicates, conservative structural conflicts, stale
  areas, missing coverage, missing files, broken references, and checksum
  failures.
- Expose GET-only health, review queue, and item-detail APIs.
- Explain every flag with evidence, source records, confidence, and a suggested
  owner action.
- Make zero automatic modifications and create no second review store.

Review and implementation evidence:

- `docs/milestone-78-architecture-review.md`
- `docs/milestone-78-engineering-review.md`
- `docs/milestone-78-status.md`
- `docs/milestone-78-acceptance.md`
- `docs/milestone-78-release-report.md`

## Development System Foundation - Governance Insertion

**Status (9 August 2026): complete and authoritative on `main` through PR #31
at merge commit `8ba8c92cc7ff596557bf4df78a6ce2d3e3b28689`. This was governance-only
work and made no NOVA runtime change.**

- Add repository-wide durable instructions in root `AGENTS.md`.
- Establish the full discuss-to-owner-acceptance development playbook.
- Define owner, product, engineering, Codex, Remote, GitHub, and Windows
  runtime responsibilities and authority boundaries.
- Record a current-capability matrix and require verification before building
  replacements for existing platform features.
- Make ChatGPT/Codex Remote on phone the primary remote development control
  surface over the Windows PC.
- Record the owner's physical verification of phone Remote against PC chats.
- Keep this insertion documentation-only with no NOVA runtime change.

Foundation documents:

- `AGENTS.md`
- `docs/engineering-principles.md`
- `docs/development-playbook.md`

## Milestone 79 - Librarian Daily-Use Validation

**Status (9 August 2026): in progress. The owner-approved plain-language
correction from PR #34 is merged, installed, and technically verified against
NOVA 0.78.2. Physical owner acceptance remains required. No detection-rule or
authority change has been made.**

- Validate explanations, issue ordering, and review links on PC and phone.
- Measure false-positive friction before changing any detection rule.
- Keep the Librarian read-only throughout validation.
- Require a new architecture and engineering decision before any
  approval-assisted Librarian action.

Validation evidence:

- `docs/milestone-79-librarian-daily-use-validation.md`

## Later capabilities

- NOVA Conductor unified interaction direction, phased over existing services
  before any bounded specialist-agent runtime
- Optional local or cloud AI provider adapters
- Broader project and document memory beyond the approved conversational
  knowledge implemented in Milestones 55–59
- Plugin and agent interfaces
- Broader operational monitoring and disaster recovery

Approved direction:

- `docs/conductor-interaction-north-star.md`
