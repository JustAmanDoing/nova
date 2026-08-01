# Milestone 71 - Architecture Review

**Review date:** 1 August 2026

**Reviewed proposal:** Milestone 72 Conversation Organisation

**Decision:** Passed with implementation conditions; revised owner-approved
scope remains architecture-conformant

## Architectural fit

The proposed capability fits the existing modular monolith. Conversation
creation, persistence, listing, retrieval, title assignment, and streaming
already belong to the chat module. Explicit rename, archive, restore, and local
lifecycle history extend that ownership without adding a service or a second
source of truth.

SQLite remains authoritative for conversation metadata and messages. The chat
service remains the only domain layer allowed to change conversation state.
The existing frontend continues to call the same local same-origin API.

## Required boundaries

1. Add nullable archived and trashed timestamps to the existing conversation
   record.
2. Add an append-only conversation-lifecycle event table for created, renamed,
   archived, and restored events.
3. Use a migration after current schema 16; do not rewrite existing messages.
4. Keep active conversations as the default list so current clients retain
   predictable behavior.
5. Require the existing local-intent header for rename, archive, restore,
   move-to-Trash, and restore-from-Trash.
6. Do not allow a message to be sent to an archived conversation.
7. Keep archived conversations directly retrievable for review, but read-only
   until the owner restores them.
8. Archive and Trash must never delete, truncate, summarize, export, upload, or
   rewrite messages.
9. Rename must preserve the previous and new title in the lifecycle event.
10. Disable lifecycle changes while that conversation is generating a reply.
11. Keep all data under the existing local database, backup, restore, and
    privacy boundaries.
12. Keep Ollama optional for every lifecycle operation.

## Explicit exclusions

- permanent deletion;
- automatic retention periods;
- automatic archival or cleanup;
- AI-generated folders, labels, categories, or archive decisions;
- full-text or semantic message search;
- conversation export, sharing, or cloud synchronization;
- folders, tags, pinning, bulk actions, merging, or splitting;
- changes to knowledge, Intake, Focus, Tailscale, or action authority;
- a new database, service, worker, provider, plugin, or agent.

## Privacy and safety review

Pass with conditions.

- Explicit owner action initiates every mutation.
- Archive is reversible and preserves the complete source record.
- No conversation content leaves the current machine or authenticated
  tailnet.
- No model classifies, renames, or reorganises the owner's history.
- Append-only lifecycle events make corrections and state transitions
  auditable.
- Existing verified backup and restore remain the recovery boundary.
- The phone transcript uses a bounded local scroll region, opens at the latest
  exchange, and preserves chronological message order.
- Phone history and lifecycle actions use a temporary local drawer; they do not
  create another persistence, navigation, or authority boundary.
- Trash is reversible and is not represented as permanent erasure.

The implementation must not expose personal conversation titles in logs,
telemetry, release evidence, test fixtures, or error messages beyond the
owner's local interface.

## Modular-monolith decision

No architectural decomposition is justified. The expected data volume and
single-owner workload are small, the chat service already owns the relevant
transactions, and no independent scaling or availability boundary exists.

## Architecture acceptance conditions

- Migration preserves every current conversation and message.
- Default active listing does not surface archived records.
- Explicit archived listing and direct record review remain available.
- Restore returns the record to the active list without duplication.
- Archived send attempts fail deterministically without writing a message.
- A failed lifecycle write leaves conversation state and audit history
  transactionally unchanged.
- Backup, restore, database integrity, loopback binding, private Serve, and
  Funnel-off checks remain green.

## Conclusion

The revised, owner-approved Milestone 72 proposal remains
architecture-conformant. Implementation must stay within the bounded runtime
and reversible-data conditions above.
