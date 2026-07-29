# Milestone 62 - Architecture Review

**Review date:** 30 July 2026

**Selected slice:** Milestone 63 - Explicit Local Document Context

**Decision:** Approved as a bounded proposal; runtime work awaits owner
approval

## Existing components to reuse

- `IntakeService` already owns local file inventory, current source metadata,
  SHA-256 fingerprints, understanding state, and extracted text.
- `ChatService` already owns conversation history, local Ollama prompts,
  streaming responses, completed-message persistence, and approved-knowledge
  citations.
- SQLite already stores bounded extracted text and ordered schema migrations.
- The React chat interface already displays source evidence without exposing
  hidden knowledge files.
- Docker Compose already keeps the API, chat provider, source files, and
  database local.

No external library or service is required for the first slice.

## Proposed flow

1. The chat interface lists safe intake metadata through the existing local
   API.
2. The owner explicitly selects one ready document for one turn.
3. The request includes the selected file identifier.
4. Before the user message is stored, the backend verifies:
   - the file record still exists;
   - understanding is ready;
   - the current source remains inside the intake root;
   - the source file still exists;
   - its SHA-256 still matches the indexed fingerprint; and
   - extracted UTF-8 text is present and within the approved context limit.
5. The backend adds the verified document as untrusted reference context
   immediately before the current user message.
6. The local model may cite the source as `[D1]`.
7. A completed assistant message stores immutable document-citation evidence.

## Preserved boundaries

- Explicit owner selection is required for every document-assisted turn.
- No automatic document retrieval or selection.
- No semantic or vector search.
- No document upload through chat.
- No access to unindexed host folders.
- No external provider or network path.
- No file move, edit, overwrite, deletion, or sharing.
- Extracted full text is not returned to the browser.
- Existing owner-approved knowledge retrieval remains separate.
- Existing file approval and execution boundaries remain unchanged.
- Original documents remain authoritative.
- Modular-monolith deployment remains unchanged.

## Prompt-injection boundary

Document text is untrusted data, not an instruction source. The local system
prompt must delimit it, direct the model not to follow instructions found
inside it, and make clear that NOVA has no tool or file-action authority from a
document.

This control reduces prompt-injection risk but does not claim perfect model
obedience. The stronger protection is architectural: this slice grants the
model no tools, filesystem action, external network access, or autonomous
permission.

## Storage and migration

The first implementation may add ordered migration 15 for a dedicated
`chat_message_document_sources` table. It should store citation metadata and
the verified source fingerprint used for that answer, not a second copy of the
document text.

The current extracted text in `understanding_results` remains derived local
data. No new vector index or document database is justified.

## Scope limits

- One explicitly selected document per turn.
- Only currently indexed intake documents with `ready` understanding.
- Maximum 8,000 UTF-8 bytes of extracted document context.
- Oversized, missing, changed, stale, failed, empty, duplicate-only, or
  unsupported records fail clearly before the turn is stored.
- Filed-library documents and arbitrary `N:\Nova\Documents` content are not
  included in this slice.

## Architecture judgement

The proposal is proportionate and preserves the current architecture. It
creates a narrow bridge between two existing modules rather than a new
subsystem. It is approved for implementation only after explicit owner
approval of the exact Milestone 63 scope.
