# Milestone 71 - Engineering Review

**Review date:** 1 August 2026

**Reviewed proposal:** Milestone 72 Conversation Organisation

**Decision:** Passed with conditions; owner-approved implementation may proceed

## Existing components to reuse

- chat conversation service and schemas;
- SQLite migration registry and transaction helpers;
- local-intent mutation guard;
- current title validation and conversation-not-found handling;
- active conversation list and accepted phone picker;
- Focus-style lifecycle and audit patterns where they fit;
- verified database backup, restore, and integrity controls;
- responsive CSS and frontend testing setup;
- protected GitHub backend, frontend, Windows, and production-runtime checks.

No external dependency or open-source package is required for this slice.

## Proposed implementation shape

### Database

- Schema migration 17 adds `archived_at` and `trashed_at` to
  `chat_conversations`.
- Add `chat_conversation_events` with an immutable identifier, conversation
  identifier, event type, previous title when applicable, new title when
  applicable, and UTC creation time.
- Backfill one `created` event only if it can be done deterministically from the
  existing conversation creation timestamp; otherwise document pre-migration
  history as unavailable rather than inventing events.
- Add an index supporting active-first updated ordering and an event index by
  conversation and creation order.

### Domain service

- Add explicit `rename`, `archive`, `restore`, `trash`, `restore_from_trash`,
  and `list_events` operations.
- Perform each state update and lifecycle insert in one database transaction.
- Reject blank or over-length titles with the existing 120-character limit.
- Reject archive of an already archived conversation and restore of an active
  conversation with a clear conflict response.
- Reject sending a message to an archived conversation before adding the user
  message.

### API

- Extend list conversations with an explicit
  `status=active|archived|trash|all` query, defaulting to active.
- Add guarded rename, archive, restore, move-to-Trash, and restore-from-Trash
  endpoints under the current conversation resource.
- Add a read-only lifecycle-events endpoint.
- Keep existing response fields compatible and add archived state explicitly.

### Frontend

- Keep active conversations in the accepted desktop list and phone picker.
- Keep newest activity first and open each conversation at its latest exchange.
- Add an always-visible phone **New chat** action and a **Jump to latest**
  control when the owner reviews older messages.
- Add a phone **Chats** drawer so selection and reversible lifecycle controls
  remain reachable without lengthening the primary chat journey.
- Add one unobtrusive owner menu for Rename and Archive on an active
  conversation.
- Add a collapsed Archived conversations view with Restore.
- Add a collapsed Trash view with Restore; do not add permanent purge.
- Show an archived conversation as read-only and prevent message submission.
- If the selected conversation is archived, move the active selection to the
  next available record or an empty new-conversation state.
- Keep all lifecycle controls at least 44 pixels on phone and keyboard usable.

## Required automated tests

1. Migration preserves existing conversations and messages.
2. A new installation creates the final schema directly.
3. Rename strips surrounding whitespace, enforces length, and records the old
   and new titles.
4. Archive preserves all messages, removes the record from the default active
   list, and records one event.
5. Restore returns the same record without duplication and records one event.
6. Repeated or invalid state transitions fail without partial writes.
7. Missing local-intent headers reject all lifecycle mutations.
8. An archived conversation cannot accept a user message.
9. Active, archived, and all listing filters return deterministic ordering.
10. The active phone picker excludes archived records.
11. Archived review and Restore work at desktop and 390-pixel layouts.
12. Lifecycle controls are disabled during streaming generation.
13. A 79-message phone transcript remains bounded, opens at the latest
    exchange, and exposes Jump to latest after scrolling upward.
14. Move-to-Trash and restore preserve every message and lifecycle event.
15. The phone Chats drawer exposes selection and lifecycle controls without
    horizontal page overflow.
16. Backend lint, strict typing, tests, and coverage remain green.
17. Frontend lint, tests, static typing, and production build remain green.
18. Windows controls, Compose validation, production build, runtime health,
    database integrity, backup, restore, private HTTPS, and Funnel-off checks
    remain green.

## Failure and recovery behavior

- Database failure returns a bounded local error and leaves state unchanged.
- Frontend refresh failure keeps the currently loaded conversation visible and
  offers retry.
- A lifecycle failure never removes messages from the displayed history.
- Restore rollback uses the existing verified-backup procedure; no new recovery
  mechanism is introduced.
- No script may delete a conversation or database during acceptance.

## Engineering risks

| Risk | Control |
| --- | --- |
| An archive hides the current conversation unexpectedly | Require an explicit confirmation and select a predictable active fallback. |
| Rename loses the previous title | Store both titles in the append-only lifecycle event. |
| Archive occurs while a reply is streaming | Disable the control and enforce service state checks. |
| Existing clients unexpectedly lose records | Default only the list endpoint to active and test explicit archived/all access. |
| Migration fabricates historical events | Backfill only deterministic creation facts; document unavailable history. |
| UI becomes crowded again on phone | Use one compact owner menu plus collapsed archive and Trash views; validate 390 pixels and physical phone. |
| A long transcript expands the entire page | Give the chat workspace a bounded viewport, keep transcript scrolling internal, and test a 79-message fixture. |
| Delete wording implies irreversible erasure | Label the action Move to Trash, explain recovery, and defer permanent purge. |

## Review conclusion

The revised proposal is bounded, testable, and implementable inside the current
architecture. It should remove the measured phone transcript defect and reduce
chat-list friction without permanent deletion or an external dependency. The
owner has approved this bounded implementation.
