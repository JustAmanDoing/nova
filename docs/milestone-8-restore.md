# Milestone 8 — Guarded database restore

## Purpose

Nova 0.8.0 can restore a verified local SQLite backup without allowing the
restore operation to overlap scans, reviews, file actions, undo, or backup
creation. The workflow is intentionally limited to database recovery.
Document files remain under user control.

## Restore sequence

1. Require the exact phrase `RESTORE <backup filename>`.
2. Resolve the requested file within the configured backup folder.
3. Verify its SHA-256 sidecar and run `PRAGMA integrity_check`.
4. Acquire the same operation lock used by the intake and execution pipeline.
5. Create and verify a new safety backup of the current database.
6. Copy the requested backup to a unique temporary path and verify the copy.
7. Atomically replace the live database.
8. Reapply additive schema initialization and reconcile the derived intake
   inventory with document files currently on disk.
9. Verify the live database again.
10. Record the result in `data/backups/restore-audit.jsonl`.

If any validation fails after replacement, Nova atomically restores the
pre-restore safety snapshot and reports the failure. If both restore and
rollback fail, Nova reports a critical stop-and-preserve-data instruction
instead of continuing silently.

## Scope and safety

Restore can change extracted text, recommendations, approvals, inventory
records, and action history because those live in SQLite. It cannot restore
document contents and does not move, remove, recreate, or overwrite any
document file.

The current intake folder remains the source of truth for which source files
exist. Nova therefore reconciles inventory after a database restore. A backup
may contain sensitive extracted text and should remain private.

## Deliberate limitations

- Restore is initiated manually from a verified backup in the local dashboard.
- Nova does not schedule restores or choose a backup automatically.
- Backup retention and off-device replication remain user-managed.
- The JSONL restore audit is local and append-only by application behavior; it
  is not a cryptographically tamper-evident ledger.
