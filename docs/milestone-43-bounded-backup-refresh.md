# Milestone 43 — Bounded Backup Refresh

Nova 0.43.0 prevents a growing recovery history from creating unnecessary
background disk work.

## Behavior

- Live intake, review, action, recovery, learning, and operational information
  retains the existing bounded five-second foreground refresh.
- Backup history loads with the initial dashboard data.
- Automatic backup-history refresh occurs at most once per minute.
- Manual actions still request a complete refresh immediately.
- Hidden tabs continue to pause all dashboard refresh work.
- Only one automatic request batch can be active at a time.

Backup creation, checksum verification, download, restore, and retention
behavior are unchanged.

## Why this matters

Listing backups reads file metadata and each checksum sidecar. That work is
small for the current recovery history, but repeating it every five seconds
scales with every retained backup even though the list rarely changes. A slower
cadence preserves visibility while keeping normal intake activity responsive.

## Verification

The frontend suite uses controlled time to confirm that:

- the initial request loads backup history;
- the five-second cycle refreshes live intake state without reloading backups;
  and
- backup history is refreshed when the minute boundary is reached.
