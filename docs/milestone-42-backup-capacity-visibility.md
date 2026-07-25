# Milestone 42 — Backup Capacity Visibility

Nova 0.42.0 shows how much local storage the complete retained backup history
uses.

## Behavior

When at least one backup exists, the dashboard summarizes:

- the total number of retained backups;
- their combined file size;
- how many have valid checksum sidecars; and
- how many need attention because verification is unavailable.

The summary uses the complete backup list even while the dashboard is showing
only the newest five entries. It is read-only and never deletes, prunes, moves,
or modifies a backup.

## Why this matters

Nova deliberately keeps every recovery point until the user chooses a retention
policy. Showing the aggregate size makes growth visible before backups compete
with documents, indexes, models, or Windows for limited local storage.

## Verification

The frontend suite supplies eight retained backups and confirms that the
dashboard reports all eight, their exact combined size, and their verification
state while the history list remains compact by default.
