# Milestone 57 — Architecture Review

**Review date:** 28 July 2026

**Base commit:** `92b7be64ea0f029a1a8d4c883b8f49162dbdf1a5`

**Working branch:** `agent/milestone-57-knowledge-lifecycle`

**Decision:** Passed

## Finding

Milestone 57 preserves NOVA's approved modular-monolith architecture. The
existing knowledge service owns duplicate assessment, revision history,
retirement, retrieval eligibility, and knowledge snapshots. The existing API
and React interface expose those controls without adding a second application,
database, background worker, provider, plugin, agent, or cloud dependency.

## Data model

Database migration 14 adds:

- optional duplicate evidence to pending knowledge candidates;
- active or retired state, current revision, update time, and retirement time
  to approved records;
- immutable `knowledge_record_revisions`; and
- append-only `knowledge_record_events`.

Existing approved records are imported as revision 1 with a recorded creation
event. The current `knowledge_records` row is a pointer to the active revision;
the revision table and Markdown files retain the historical evidence.

## Safety boundaries

- Duplicate assessment is deterministic and local.
- A likely duplicate cannot be preserved separately unless the owner selects
  the separate-record control.
- Updates create a new file and revision. They never overwrite an earlier
  Markdown copy.
- Retirement changes retrieval eligibility but never deletes a Markdown file,
  revision, event, conversation, or citation.
- Every lifecycle change requires the existing local-action intent guard.
- Snapshot creation verifies the path and SHA-256 of every tracked revision
  before writing an archive. Any mismatch fails closed.
- Snapshots are stored beneath NOVA's configured local backup root with an
  external SHA-256 sidecar.
- Retrieval continues to use active, owner-approved, checksum-verified records
  only.
- The API and browser remain loopback-only.

## Complexity review

SQLite tables and a standard ZIP archive are sufficient for the measured
requirements. A vector database, event broker, separate memory service, or
automatic consolidation engine would add operational risk without evidence of
need. They remain deferred.

## Acceptance result

The production Windows stack applied migration 14 successfully and retained
SQLite integrity. A representative record completed duplicate review, update,
active retrieval, retirement, and snapshot verification. Existing approved
records remained available. The architecture conditions therefore passed.
