# Milestone 52: On-demand database integrity

Nova already verifies the active database before migrations and verifies every
backup before publication or restore. The Windows status control previously
proved that the containers and API were responsive, but did not independently
recheck the active SQLite file.

## Change

- `GET /api/v1/system/integrity` opens the active database read-only.
- The endpoint runs SQLite's bounded `PRAGMA quick_check`.
- The check shares Nova's operation lock so it cannot overlap a move, undo,
  restore, backup, or intake scan.
- The response reports `ok` or `failed`, a timestamp, and safe guidance without
  exposing a local path or database error details.
- **Check Nova.cmd** now runs the check after service, version, storage, and scan
  status checks.
- A failed database check causes the Windows status request to fail clearly and
  directs the user to stop Nova and restore a verified backup.

The dashboard's frequent refresh does not call this endpoint. Integrity work is
therefore performed only on explicit request, avoiding repeated full-database
checks as the local index grows.

## Verification

Backend tests confirm that the endpoint does not change a healthy database and
that a damaged database returns safe failure guidance. Windows structural tests
require the on-demand check and its timeout. The production workflow calls the
endpoint against the running container stack.
