# Milestone 57 — Knowledge Lifecycle and Duplicate Controls

**Date:** 28 July 2026

**Base commit:** `92b7be64ea0f029a1a8d4c883b8f49162dbdf1a5`

**Working branch:** `agent/milestone-57-knowledge-lifecycle`

**Prototype release:** 0.57.0

**Decision:** Engineering release-readiness passed; owner acceptance pending

## Scope delivered

- Identify deterministic likely duplicates among active approved records.
- Show the matching title and relative path before approval.
- Require explicit confirmation to create a separate likely duplicate.
- List active and retired approved records in the owner interface.
- Update an active record only by creating a new immutable Markdown revision.
- Preserve earlier revision files and append lifecycle evidence.
- Retire a record only after a record-specific typed confirmation.
- Exclude retired records from future retrieval without deleting history.
- Create a verified local knowledge snapshot with a manifest, every tracked
  revision, archive-integrity testing, and a SHA-256 sidecar.
- Fail retrieval, updates, retirement, and snapshots closed when tracked
  knowledge fails its path or checksum verification.

## Duplicate policy

Duplicate detection is advisory and deterministic. Exact normalized content is
a duplicate. A same-kind record with at least 0.8 token similarity is a likely
duplicate. Nova does not merge, overwrite, or delete either record
automatically. The owner may revise the proposal, reject it, or explicitly keep
both separately.

The backend recalculates duplicate status at approval and update time. The
interface offers the separate-record control even when a duplicate appears
only after the owner edits a proposal or revision.

## Lifecycle policy

The current approved record is active or retired. An update:

1. verifies the current file path and SHA-256;
2. checks for another active likely duplicate;
3. writes a unique no-overwrite Markdown file;
4. records its SHA-256 and revision metadata;
5. updates the current record pointer; and
6. appends an update event.

Retirement verifies the current file, requires `RETIRE <record-id-prefix>`,
marks the record retired, and appends an event. It does not remove any file.

## Snapshot policy

Knowledge snapshots are independent from SQLite database backups. Before
creating a snapshot, Nova verifies every path and SHA-256 stored in
`knowledge_record_revisions`. The ZIP contains:

- `manifest.json`; and
- one copy of every tracked Markdown revision beneath `knowledge/`.

Nova tests the completed ZIP and writes a filename-bound `.zip.sha256`
sidecar. A missing, escaped, unreadable, changed, or duplicate archive path
stops the operation before a successful snapshot is reported.

## Automated verification

The complete automated matrix passes:

- 122 backend tests at 92.42% coverage;
- strict backend lint and type checking;
- 29 frontend tests;
- frontend lint and type checking;
- production frontend build;
- production backend and frontend image builds;
- Compose validation;
- Windows controller structural validation; and
- Git whitespace validation.

## Pre-install checkpoint

Before implementation testing, a verified SQLite backup was created:

`nova-20260728T101442.596458Z.db`

SHA-256:

`5f6533cd992342e1c4d431c70ed30f9ccd741d2f8eafdfaff2c4850ee328ea9d`

The database backup, a copy of the existing knowledge directory, and a
knowledge-file SHA-256 manifest are stored under:

`N:\Nova\Backups\Pre-Milestone-57`

## Live acceptance evidence

- Installed production version: 0.57.0.
- Recorded schema migration: 14, `knowledge-lifecycle-and-duplicates`.
- Live and exported database integrity: `ok`.
- Exact duplicate score: 1.0.
- Unconfirmed duplicate approval: blocked with HTTP 409.
- Update: revision 1 retained; revision 2 created at a new path.
- Active retrieval: `golden comet [K1]` from revision 2.
- Incorrect retirement phrase: blocked with HTTP 422.
- Retirement: revision 3, files retained, record excluded from retrieval.
- Knowledge snapshot:
  `nova-knowledge-20260728T104124.612501Z.zip`.
- Knowledge snapshot SHA-256:
  `497f0d9a7962936dbfcef2a6a3fcba0e0afeaaad03cf230c2a42d8a0308810c9`.
- Snapshot manifest: 4 records, 6 revision rows, 5 unique knowledge files.
- Independent archived-revision checks: 6 passed, 0 failed.
- Post-acceptance database:
  `nova-20260728T104149.102356Z.db`.
- Post-acceptance database SHA-256:
  `dab9874386ef89223c41a7dfc8ee9d26ccb2f616ca1ac7e1025c57dd859ec4f1`.
- Post-acceptance database and snapshot copies:
  `N:\Nova\Backups\Post-Milestone-57`.
- Desktop and 390 px browser checks passed after correcting the conversation
  strip's horizontal overflow. No console errors remained.

## Release-readiness decision

Milestone 57 passes architecture and engineering release-readiness. Owner
acceptance remains pending. The synthetic lifecycle record is intentionally
retired and retained as acceptance evidence.

No merge to `main` or remote push is part of this milestone.

## Exact next action

Complete the short owner acceptance check in the installed Chat interface.
After acceptance, select the scope of Milestone 58 before adding another
runtime capability.
