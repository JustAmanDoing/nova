# Milestone 72 Proposal - Conversation Organisation

**Proposal date:** 1 August 2026

**Proposed base:** accepted release 0.70.0

**Status:** Awaiting explicit owner approval

## Goal

Keep NOVA's growing local chat history useful on phone and PC by letting the
owner rename, archive, review, and restore conversations without deleting or
rewriting any message.

## Owner experience

### Rename

1. The owner opens the current conversation menu.
2. NOVA shows the existing title in an editable field.
3. The owner confirms the replacement title.
4. NOVA updates the visible title and records the previous and new values in
   local lifecycle history.

### Archive

1. The owner chooses **Archive conversation**.
2. NOVA explains that every message will be preserved and the conversation can
   be restored.
3. The owner confirms.
4. NOVA removes it from the default active list and shows a predictable active
   fallback or an empty new-conversation state.

### Review and restore

1. The owner opens the collapsed **Archived conversations** view.
2. The owner may open an archived conversation in read-only mode.
3. The owner chooses **Restore** to return the same conversation to the active
   list.

## Required behavior

- Active conversations remain the default desktop list and phone picker.
- Archived conversations are hidden from that default list but not deleted.
- The owner can deliberately list and review archived conversations.
- Archived conversations cannot accept a new message until restored.
- Rename, archive, and restore require the existing local-intent guard.
- Lifecycle state and audit event commit atomically.
- The complete message history, model metadata, timestamps, knowledge sources,
  and document citations remain unchanged.
- The feature works without Ollama.
- The phone interface keeps a clear primary chat journey and 44-pixel controls.

## Data and API boundary

- Extend the existing local conversation table with archived state.
- Add one local append-only lifecycle-event table.
- Keep the current chat service as the only conversation writer.
- Extend the existing same-origin local API; add no listener or service.
- Reuse the current SQLite backup, restore, integrity, and migration system.

## Explicit exclusions

- deletion or bulk deletion;
- automatic archiving, cleanup, or retention;
- AI-generated folders, categories, labels, or archive choices;
- folders, tags, pinning, merging, or splitting conversations;
- message editing or summarization;
- full-text or semantic conversation search;
- export, upload, sharing, sync, or another account;
- notification, reminder, calendar, voice, plugin, or agent work;
- any change to Knowledge, Focus, Intake, document, or filing authority.

## Acceptance criteria

1. All existing conversations and messages survive migration unchanged.
2. The owner can rename an active conversation and inspect its lifecycle event.
3. The owner can archive a conversation and confirm it disappears from the
   default active list without losing messages.
4. Direct review of the archived conversation still shows the complete history.
5. Sending to an archived conversation is rejected without writing a message.
6. Restore returns the same identifier, title, messages, citations, and model
   metadata to the active list.
7. Invalid and repeated lifecycle actions are clear and transactionally safe.
8. Missing local intent rejects each lifecycle mutation.
9. Desktop keyboard and physical-phone journeys pass.
10. Backend, frontend, Windows, production-container, database-integrity,
    backup, restore, private HTTPS, and Funnel-off checks pass.
11. Changed-file review finds no secret, personal fixture, generated artifact,
    debug code, or unrelated change.
12. Owner acceptance passes before release.

## Release boundary

If approved, this proposal authorises only the bounded Milestone 72 runtime
slice above. It does not authorise any excluded capability or a release until
implementation, architecture, engineering, automated, runtime, recovery,
desktop, and physical-phone acceptance all pass.

## Approval requested

Approve Milestone 72 to implement explicit local conversation rename, archive,
review, restore, and lifecycle audit with no deletion or automation.
