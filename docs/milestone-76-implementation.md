# Milestone 76 - Local NOVA Project Record Implementation

**Date:** 3 August 2026

**Target release:** 0.76.0

**Status:** Implemented and owner accepted; protected repository integration
and exact merged-main release verification remain

## Owner outcome

NOVA now keeps its verified project record on the local `N:` drive instead of
depending on ChatGPT conversations as the only place where project context can
be found. The record is inspectable from NOVA on PC and through NOVA's existing
private Tailscale address.

The migration is deliberately truthful: repository evidence, runtime status,
approved knowledge, dated archives, and the supplied ChatGPT project snapshot
are local. Raw ChatGPT conversations that the owner has not explicitly supplied
are not claimed as migrated.

## Implemented

- Added a checksum-bound archive index at
  `N:\Nova\Archive\archive-index.json`.
- Added a canonical current-status record at
  `N:\Nova\Archive\Current\NOVA-Current-Status.md`.
- Preserved an exact Release 0.74.0 repository-document snapshot under
  `N:\Nova\Archive\Repository\v0.74.0`.
- Preserved the available ChatGPT project source snapshot as supporting,
  non-authoritative evidence under `N:\Nova\Archive\Imported`.
- Added an append-only dated migration session record.
- Added a read-only Project Record API and `/archive.html` view.
- Added **Record** to NOVA's primary navigation.
- Added bounded verified text previews without browser filesystem access.
- Corrected an owner-found phone defect where a selected preview was rendered
  after the complete source catalogue and therefore appeared not to open. At
  phone width, a selected document now opens immediately in a fixed, internally
  scrollable panel with focused **Close** control and Escape-key dismissal.
- Added a guarded Windows control for refreshing the project record.
- Added a guarded Windows control for importing one explicitly selected
  NOVA-only source.
- Added typed confirmation, duplicate detection, SHA-256 verification,
  no-overwrite behavior, size and extension bounds, and rejection of a full
  ChatGPT `conversations.json` account export.
- Kept imported raw chat evidence separate from approved knowledge and outside
  Git.

## Verified migrated state

- Local sources indexed: 142.
- Sources passing SHA-256 verification: 142.
- Changed, missing, or invalid sources: 0.
- Raw NOVA chat sources explicitly supplied: 0.
- Approved knowledge remains in `N:\Nova\Memory`.
- NOVA's runtime conversations remain in its local SQLite database and verified
  backups.

## Architecture, safety, and privacy

- The implementation remains inside NOVA's modular monolith.
- The runtime archive service is read-only.
- Docker mounts `N:\Nova\Archive` at `/project-archive` with `RW=false`.
- Archive mutation is available only through explicit host-side controls.
- Original files are never overwritten during import.
- Raw sources do not become approved knowledge automatically.
- NOVA does not access the owner's ChatGPT account, credentials, unrelated
  chats, or full account export automatically.
- Docker remains loopback-only; phone access remains tailnet-only through the
  existing Tailscale Serve route with Funnel off.
- No external provider, semantic search, plugin, agent, background sync, or
  autonomous action was added.

## Recovery evidence

Before installing the candidate runtime, NOVA created backup
`nova-20260803T090345.816532Z.db`. Its recorded SHA-256 is:

`200faef35f783653cb368205c3a3c475597b5f0d5a251f326c64b9640323d850`

The pre-Milestone-76 archive index and current-status record were also copied to
`N:\Nova\Backups\Pre-Milestone-76` before installation.

## Remaining boundary

No verbatim ChatGPT conversation has been supplied for production import yet.
That requires one owner-controlled export or copied conversation source. Until
then, NOVA accurately reports zero raw chat sources rather than pretending that
ChatGPT history was migrated.

## Exact next action

Integrate through the protected pull-request workflow, rebuild from exact merged
`main`, refresh the canonical local record, and publish Release 0.76.0.
