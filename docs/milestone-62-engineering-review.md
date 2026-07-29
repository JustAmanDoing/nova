# Milestone 62 - Engineering Review

**Review date:** 30 July 2026

**Selected slice:** Milestone 63 - Explicit Local Document Context

**Decision:** Feasible and recommended; implementation awaits owner approval

## Feasibility findings

The current code already provides most required primitives:

- `understanding_results.full_text` stores locally extracted text.
- `intake_files` stores the authoritative indexed fingerprint and relative
  path.
- `IntakeService` serializes database and file operations with its existing
  lock.
- `ChatService.begin_turn` and `add_approved_knowledge_context` provide a clear
  point for validated context composition.
- the chat endpoint already preserves incomplete-generation behavior;
- knowledge-source persistence and rendering provide a tested citation
  pattern; and
- migration, backup, restore, repository hygiene, and production-runtime tests
  already cover the surrounding safety systems.

The first slice needs no new open-source dependency. Reusing existing NOVA
services is simpler and safer than importing a RAG framework.

## Required implementation areas

### Backend

- Add a typed optional selected-document identifier to the send-message
  request.
- Add one bounded service method that resolves and revalidates a ready intake
  document without returning full text through the API.
- Reject invalid selection before persisting the user turn.
- Add untrusted `[D1]` document context separately from owner-approved `[K#]`
  personal knowledge.
- Persist citation metadata only after a completed assistant response.
- Add ordered migration 15 and restore/migration coverage if a dedicated
  citation table is used.

### Frontend

- Add an explicit one-document selector using safe existing intake metadata.
- Show the selected filename before send and allow removal.
- Clear or retain selection predictably after send.
- Render `[D1]` source evidence separately from `[K#]` personal knowledge.
- Announce selection, validation errors, and source evidence accessibly.

### Documentation and operations

- Explain that document context is explicit, local, bounded, and untrusted.
- Keep the supported Windows start, update, status, backup, and restore paths.
- Preserve version alignment across backend, frontend, runtime, and tests.

## Required tests

1. A ready unchanged document is added to one turn.
2. The model prompt labels the document as untrusted `[D1]` reference data.
3. A completed answer persists and returns exact citation evidence.
4. A turn without selection behaves exactly as release 0.59.0.
5. Missing, changed, outside-root, stale, non-ready, empty, and oversized
   selections are rejected before message persistence.
6. Document full text is never returned by the intake or chat metadata API.
7. Stopping generation does not fabricate a completed answer or citation.
8. Provider failure preserves the existing user-message behavior and does not
   create assistant citation evidence.
9. Owner-approved `[K#]` knowledge and explicit `[D1]` context remain
   distinguishable when both are present.
10. Migration, backup, restore, and downgrade guards remain correct.
11. Keyboard, screen-reader, narrow-window, and visible-source acceptance pass.
12. Production containers make no internet document or model request.

## Delivery assessment

A focused implementation should fit one bounded milestone because it reuses
the current extraction, chat, citation, migration, and local-runtime
infrastructure. Broad document search, multi-document context, chunking,
embeddings, library indexing, and remote access must not enter the slice.

## Risks

- A document may contain prompt-injection text.
- Long documents may exceed the local model context.
- A source may change between indexing and use.
- Citation evidence may become misleading if it is not bound to the exact
  verified fingerprint.
- Combining `[K#]` and `[D1]` sources may confuse the model or interface.

The proposed system prompt, explicit selection, byte limit, current SHA-256
verification, separate source types, and no-tool architecture bound these
risks sufficiently for a prototype.

## Engineering judgement

Milestone 63 is the highest-value low-complexity next slice supported by
current evidence. The proposal is ready for an owner decision. No runtime
implementation, version change, or migration is authorized by this review.
