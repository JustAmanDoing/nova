# Milestone 41 — Backup History Visibility

Nova 0.41.0 makes every retained recovery point accessible without making the
normal dashboard unnecessarily long.

## Behavior

- The five newest database backups remain visible by default.
- When more backups exist, **Show all** reveals the complete retained history.
- **Show latest 5** returns to the compact view.
- The toggle reports its expanded state and identifies the controlled history
  list for assistive technology.
- Download, checksum, restore confirmation, and integrity safeguards are
  unchanged for every backup.

Nova still never deletes or prunes a backup automatically. The full-history
view only changes what is visible in the dashboard.

## Verification

The frontend test suite supplies eight retained backups and confirms that:

- only the newest five appear initially;
- the exact retained count is included in the control;
- all eight become accessible on request; and
- the compact view can be restored without changing backup data.
