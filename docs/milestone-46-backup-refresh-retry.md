# Milestone 46 — Prompt Backup Refresh Retry

Nova 0.46.0 retries a failed automatic backup-history refresh on the next
dashboard cycle.

## Behavior

- The automatic refresh records its one-minute backup-history checkpoint only
  after the complete dashboard request succeeds.
- A failed or superseded request does not advance that checkpoint.
- The next visible five-second dashboard cycle therefore retries backup
  history promptly.
- Successful backup-history requests retain the existing at-most-once-per-
  minute cadence.
- Manual refreshes, latest-request-wins ordering, hidden-tab pausing, and all
  backup safety behavior are unchanged.

## Why this matters

Previously, the automatic loop advanced the backup refresh timestamp even when
the request failed. A short network or service interruption could therefore
hide a newly created recovery point for almost a minute after Nova recovered.

Retrying on the next normal cycle restores visibility quickly without creating
an aggressive independent retry loop.

## Verification

The frontend suite forces the first backup inventory request to fail, advances
controlled time by one five-second cycle, and confirms that Nova requests the
inventory again rather than waiting for the one-minute boundary.
