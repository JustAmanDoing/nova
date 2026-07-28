# Milestone 55 — Conversation-to-Knowledge Capture

**Engineering acceptance date:** 28 July 2026

**Base commit:** `9692020` (Milestone 54 local chat prototype)

**Working branch:** `agent/milestone-55-conversation-knowledge`

**Prototype release:** 0.55.0

**Decision:** Engineering acceptance passed; owner acceptance is pending

## Scope delivered

- Recognize bounded explicit requests such as `Remember that...`.
- Suggest review for a limited set of high-value profile statements:
  preferences, goals, names, dated age statements, and family-profile facts.
- Prepare one editable pending proposal with type, title, content, source,
  reason, and confidence.
- Require the explicit local **Approve & save** action before creating a
  permanent record.
- Allow **Don't save** to reject the proposal without writing a record.
- Store approved record contents and checksum in SQLite.
- Write an owner-approved, no-overwrite Markdown copy under the configured
  local knowledge directory.
- Record proposed, approved, and rejected events locally.
- Keep chat available with a truthful warning if proposal preparation fails.

## Architecture and safety boundaries

The modular monolith remains intact. Knowledge capture is a small service behind
versioned FastAPI endpoints and the existing local-action guard.

Database migration 12 adds:

- `knowledge_candidates`;
- `knowledge_records`; and
- append-only `knowledge_events`.

The detector is deterministic. The language model does not select, approve, or
write personal knowledge. A proposal can be edited before approval. Approval
uses an exclusive file create, so an existing record can never be overwritten.
If database persistence fails after a new record file is created, Nova removes
only that newly created operation artifact and reports failure.

The SQLite record contains the approved content and checksum, so verified
database backups retain the recoverable knowledge record. The Markdown copy is
an auditable local representation. The running Windows configuration binds the
knowledge directory to:

`N:\Nova\Memory`

The API and frontend remain bound to IPv4 loopback. Private-network CORS
preflight is allowed only for the already configured local frontend origins;
this does not expand the listening interface or allowed Host boundary.

## Verification evidence

### Automated matrix

- Ruff passed.
- Strict mypy passed for 31 application source files.
- 112 backend tests passed with at least 90% total coverage.
- ESLint and TypeScript passed.
- 26 frontend tests passed, including the editable approval card.
- Multi-page Vite production build passed.
- `git diff --check` passed.

The focused knowledge tests prove:

- explicit requests remain pending before review;
- approval requires the local-action header;
- edited approval creates one checksum-matched Markdown record;
- a second approval is rejected;
- rejection creates no record;
- ordinary conversation creates no proposal;
- age suggestions include the date stated;
- an occupied record path is never overwritten; and
- proposal failure warns without breaking chat.

### Live Windows and container acceptance

- A verified pre-upgrade database backup was created:
  `nova-20260728T091513.469932Z.db`.
- Backup SHA-256:
  `1f218c9dfe07d1e951abbc70e7b3b03315112b217ed1f53abdbb8d4a36aa5b0f`.
- Production backend and frontend images built successfully.
- Health reported version `0.55.0`.
- SQLite migration 12 was recorded and `PRAGMA integrity_check` returned `ok`.
- `qwen3:8b` remained available through the local provider.
- Docker mounted `N:\Nova\Memory` at `/knowledge`.
- An explicit synthetic request produced a pending proposal.
- An edited approval created a Markdown record whose host SHA-256 exactly
  matched the SQLite record.
- A browser-controlled approval initially exposed a private-network preflight
  failure. The local-origin CORS configuration was corrected and regression
  tested.
- The same visible **Approve & save** action then succeeded.
- Two browser-controlled synthetic suggestions were rejected through
  **Don't save** and created no permanent records.
- Visual inspection confirmed the review card clearly distinguishes
  **Nothing has been saved yet** from the approved result.

Two synthetic, explicitly labelled acceptance records remain under
`N:\Nova\Memory\References`. They contain no personal information and provide
runtime evidence for the knowledge-file path.

## Known limitations

- Nova does not yet retrieve approved knowledge while answering. That is
  Milestone 56.
- Exact semantic duplicate detection and record consolidation are not yet
  implemented.
- Each user message prepares at most one proposal. Compound statements are not
  split automatically.
- Approved record retirement, deletion, and editing after approval are not
  implemented.
- The Markdown directory is not independently packaged by the database-backup
  download. SQLite retains the approved contents and checksum, while the
  external `N:\Nova` backup plan must include the Markdown copies.
- Chat remains PC-local in this milestone; authentication and phone access are
  not part of this release.
- Tools, web access, RAG, voice, and autonomous actions remain disabled.

## Engineering release-readiness decision

Milestone 55 passes engineering prototype acceptance. It delivers the intended
natural conversation-to-review workflow while preserving explicit owner
approval, local storage, no-overwrite behavior, truthful pending state, and the
existing guarded intake system.

Owner acceptance should verify:

1. a `Remember that...` statement creates the expected editable review card;
2. **Don't save** removes a proposal and creates no record;
3. **Approve & save** creates a file under `N:\Nova\Memory`; and
4. ordinary chat remains usable.

The independent review records are:

- `docs/milestone-55-architecture-review.md`
- `docs/milestone-55-engineering-review.md`

## Exact next milestone

After owner acceptance, Milestone 56 — Approved Knowledge Retrieval. It must use
only owner-approved records, cite the exact local source, and state clearly when
no approved knowledge matches.
