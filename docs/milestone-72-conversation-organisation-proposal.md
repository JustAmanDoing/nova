# Milestone 72 Proposal - Conversation Organisation

**Proposal date:** 1 August 2026

**Proposed base:** accepted release 0.70.0

**Status:** Approved for bounded runtime implementation

**Owner approval:** 1 August 2026, including phone-first ease-of-use work

## Goal

Keep NOVA's growing local chat history useful on phone and PC by opening at the
latest exchange, keeping the newest conversations first, making **New chat**
easy to reach, and letting the owner rename, archive, review, restore, or move
old conversations to recoverable Trash without rewriting any message.

## Daily-use navigation

- Opening Chat selects the most recently active conversation.
- Opening or switching conversations positions the transcript at its latest
  exchange instead of making the owner scroll past the complete history.
- Messages remain chronological inside a conversation; NOVA does not reverse
  the conversation and make replies harder to follow.
- A visible **Jump to latest** control appears after the owner scrolls upward.
- **New chat** remains a clear 44-pixel action on phone and PC.
- A phone **Chats** drawer keeps conversation selection, Rename, Archive,
  recoverable Trash, and Restore reachable without scrolling away from the
  composer.
- Conversation pickers remain ordered by most recent activity.

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

### Remove from daily view

1. The owner chooses **Move to Trash**.
2. NOVA explains that the conversation will leave active and archived views but
   remains recoverable.
3. The owner confirms.
4. The owner can inspect Trash and restore the complete conversation.

Trash is NOVA's safe deletion experience for this milestone. Permanent purge
is deliberately deferred until verified backup, recovery semantics, and an
appropriate high-friction confirmation have separate evidence.

## Required behavior

- Active conversations remain the default desktop list and phone picker.
- Archived conversations are hidden from that default list but not deleted.
- The owner can deliberately list and review archived conversations.
- Archived conversations cannot accept a new message until restored.
- Trashed conversations cannot accept a new message until restored.
- Rename, archive, restore, move-to-Trash, and restore-from-Trash require the
  existing local-intent guard.
- Lifecycle state and audit event commit atomically.
- The complete message history, model metadata, timestamps, knowledge sources,
  and document citations remain unchanged.
- The feature works without Ollama.
- The phone interface keeps a clear primary chat journey and 44-pixel controls.

## Data and API boundary

- Extend the existing local conversation table with archived and trashed state.
- Add one local append-only lifecycle-event table.
- Keep the current chat service as the only conversation writer.
- Extend the existing same-origin local API; add no listener or service.
- Reuse the current SQLite backup, restore, integrity, and migration system.

## Explicit exclusions

- permanent deletion or bulk actions;
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
9. Desktop keyboard and physical-phone journeys pass, including opening and
   closing the phone Chats drawer.
10. A long physical-phone conversation opens at its latest exchange, can jump
    back to latest after review, and keeps New chat reachable.
11. Move to Trash removes a conversation from daily views without deleting its
    messages, and Restore returns the same identifier and history.
12. Backend, frontend, Windows, production-container, database-integrity,
    backup, restore, private HTTPS, and Funnel-off checks pass.
13. Changed-file review finds no secret, personal fixture, generated artifact,
    debug code, or unrelated change.
14. Owner acceptance passes before release.

## Release boundary

If approved, this proposal authorises only the bounded Milestone 72 runtime
slice above. It does not authorise any excluded capability or a release until
implementation, architecture, engineering, automated, runtime, recovery,
desktop, and physical-phone acceptance all pass.

## Approval requested

Approved: implement explicit local conversation navigation, rename, archive,
review, restore, recoverable Trash, and lifecycle audit with no permanent
deletion or automation.
