# Milestone 50 — Precise backup API states

## Outcome

Nova now distinguishes a backup that was fully verified during the current
operation from a retained backup that has a valid checksum record but has not
been re-read during history listing.

## Typed API contract

Each backup record exposes two independent states:

- `checksum_recorded` confirms that one syntactically valid, filename-bound
  SHA-256 sidecar is available.
- `verified` confirms that Nova completed the relevant SHA-256 and SQLite
  integrity checks during the current operation.

A successful backup-creation response sets both fields to `true`. A normal
history response may set `checksum_recorded` to `true`, but keeps `verified`
`false` because listing deliberately avoids hashing and opening every retained
database.

## User interface

Backup history uses `checksum_recorded` for its summary, availability wording,
download links, and restore controls. It does not use the stronger `verified`
claim for an item that has only been listed.

Download and restore remain guarded operations. They recheck the backup content
against the recorded SHA-256 value and run SQLite integrity verification before
returning or applying it.

## Compatibility

The existing `verified` field remains available for the guarded Windows updater
and restore safety-backup results. The updater continues to stop unless a newly
created pre-update backup returns `verified=true`.

## Verification

Backend tests assert the distinct create and list states. Frontend tests use
checksum availability for retained history while preserving verified creation
and restore-safety responses.
