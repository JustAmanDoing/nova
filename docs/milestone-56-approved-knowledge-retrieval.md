# Milestone 56 — Approved Knowledge Retrieval

**Engineering acceptance date:** 28 July 2026

**Base commit:** `3ff982f` (Milestone 55 accepted knowledge capture)

**Working branch:** `agent/milestone-56-approved-knowledge-retrieval`

**Prototype release:** 0.56.0

**Decision:** Accepted

## Scope delivered

- Search only owner-approved conversation knowledge.
- Exclude pending and rejected proposals from retrieval.
- Verify the approved Markdown record remains beneath the configured knowledge
  root, exists, and still matches its recorded SHA-256 before use.
- Add up to three deterministic lexical matches to the local model context.
- Require the model to cite the supplied `[K#]` label when it uses a record.
- Show the exact record title and local relative path below the answer.
- Persist a checksum-bound snapshot of each cited source with the assistant
  message so citations survive reloads and database backups.
- Show a clear no-match result when no approved record qualifies.
- Keep ordinary chat available with a truthful warning if retrieval itself
  fails.

## Architecture and safety boundaries

The modular monolith remains intact. Retrieval is implemented by the existing
knowledge, chat, and route services. It does not introduce a vector database,
new provider, plugin, agent, tool, or cloud dependency.

Database migration 13 adds:

- `chat_messages.knowledge_checked`; and
- `chat_message_knowledge_sources`.

The retrieval query joins approved records to approved candidates. Candidate
content that is still pending or was rejected cannot enter model context.
Before a source is returned, Nova resolves its Markdown path beneath the
configured knowledge root and compares its current SHA-256 with the approved
database record. Missing, escaped, or changed files fail closed.

The model receives only the matched approved records for that turn. The
frontend renders exact source metadata from the backend rather than asking the
model to invent a citation. The source snapshot is evidence for the historical
answer; the live Markdown file remains independently checksum checked for every
new retrieval.

The API and frontend remain bound to IPv4 loopback. The existing local-action
guard still protects conversation creation and message submission. General
document search, tools, web access, autonomous actions, and remote access are
not enabled.

## Verification evidence

### Automated matrix

- Ruff passed.
- Strict mypy passed for 31 application source files.
- 117 backend tests passed with 92% total coverage.
- ESLint and TypeScript passed.
- 27 frontend tests passed.
- Vite production build passed.
- Windows controller structural verification passed.
- `git diff --check` passed.

Focused regression tests prove:

- only approved records are retrieved;
- pending and rejected records are excluded;
- common spelling variants are normalized;
- a no-match result returns no source;
- a changed Markdown file fails closed;
- exact source metadata is streamed and persisted with the answer; and
- the no-match state remains explicit after persistence.

### Live Windows and container acceptance

- Production backend and frontend images built and started successfully.
- Both services remained loopback-only.
- Health reported version `0.56.0`.
- SQLite migration 13 was recorded and `PRAGMA integrity_check` returned `ok`.
- A visible browser question, `What is the automated acceptance value?`,
  answered `amber lighthouse [K1]`.
- The visible source card named
  `Milestone 55 automated acceptance record` and showed its exact local path.
- A visible no-match question, `What is my favourite fruit?`, reported
  `No approved knowledge matched this message.`
- Reloading the page preserved the citation, exact source, and no-match state.
- The live database contained one persisted citation, two
  knowledge-checked assistant messages, one no-match message, and zero pending
  candidates after the test.
- A verified post-acceptance database backup was created:
  `nova-20260728T100147.608912Z.db`.
- Backup SHA-256:
  `81d166c17ce4f58df8e70dfe4debc9e32387d48678902685e5ddcf7caef79948`.
- The exported copy is stored under
  `N:\Nova\Backups\Post-Milestone-56`.
- The copied backup passed SQLite integrity, contained migration 13, and
  retained the citation and knowledge-checked message evidence.

## Known limitations

- Matching is deterministic lexical retrieval with bounded spelling aliases,
  not embedding-based semantic search. Paraphrases without shared terms may
  produce no match.
- Retrieval covers owner-approved conversation knowledge records only. It does
  not search the intake library or arbitrary files.
- At most three records are supplied to one turn.
- Exact semantic duplicate detection and record consolidation are not yet
  implemented.
- Approved records cannot yet be edited, retired, or deleted through the
  interface.
- The Markdown directory is not independently included in a downloaded
  database backup. External backup coverage must include `N:\Nova\Memory`.
- Chat remains PC-local; authentication and phone access are not part of this
  release.
- Existing intake frontend tests continue to emit non-failing React
  `act(...)` warnings.
- Tools, web access, voice, plugins, agents, and autonomous actions remain
  disabled.

## Engineering release-readiness decision

Milestone 56 passes engineering prototype acceptance. It retrieves only
approved, checksum-verified local records; cites exact source metadata; persists
evidence; and states clearly when no approved knowledge matches. The local,
owner-controlled, no-silent-memory architecture remains intact.

## Owner acceptance

Owner acceptance passed on 28 July 2026. The installed prototype returned the
approved `amber lighthouse [K1]` answer with its exact local record and clearly
reported that no approved knowledge matched the unknown favourite-fruit
question.

No merge to `main` or remote push is part of this milestone.

## Exact next milestone

Milestone 57 should add approved-record lifecycle and duplicate controls before
retrieval expands to broader documents or embedding-based semantic search.
