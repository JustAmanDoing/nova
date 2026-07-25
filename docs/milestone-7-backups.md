# Milestone 7 — Verified local backups

## Purpose

Nova 0.7.0 can create a consistent backup of its local SQLite database while the
application remains online. This protects inventory, extracted text,
recommendations, approvals, and the append-only action audit from loss of the
Docker database volume.

## Backup sequence

1. Create a uniquely named temporary database under `data/backups`.
2. Use SQLite's online backup API to copy a transactionally consistent snapshot.
3. Run `PRAGMA integrity_check` against the snapshot.
4. Calculate a SHA-256 fingerprint.
5. Atomically publish the database and checksum sidecar.
6. List the verified backup in the local dashboard.

Failed temporary files are removed. Existing backups are never overwritten or
automatically deleted.

## Storage and privacy

Backups are stored under the host-mounted `data/backups` folder, outside Nova's
Docker database volume. A snapshot can contain extracted document text and
operational history. It must not be committed to Git or placed in public cloud
storage without an explicit privacy decision.

Docker exposes the frontend and API on `127.0.0.1` only. This preserves Nova's
local-only default while the API has no user authentication.

## Deliberate boundary

This milestone deliberately stopped at creating, listing, verifying, and
downloading backups because restore replaces live application state and
requires stronger preflight, coordination, rollback, and
explicit-confirmation safeguards. Those safeguards are implemented separately in
[Milestone 8 — Guarded database restore](milestone-8-restore.md).
