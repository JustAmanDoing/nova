# Milestone 44 — Latest Dashboard State

Nova 0.44.0 prevents a slow earlier dashboard request from replacing newer
state.

## Behavior

- Every dashboard request batch receives a monotonically increasing identifier.
- Starting a newer manual or automatic load makes every earlier batch stale.
- Only the latest batch may update files, metrics, history, backups, learning,
  operations, or the visible loading error.
- Network work already in progress is allowed to finish safely, but its result
  is ignored when it is no longer current.
- Existing hidden-tab pausing, abort handling, refresh cadence, and API
  behavior are unchanged.

## Why this matters

Manual scans, reviews, file actions, backup operations, and restores can request
fresh data while the bounded background refresh is still completing. Without
ordering, an earlier snapshot can arrive last and briefly roll the dashboard
back to obsolete information even though the server is correct.

## Verification

The frontend suite holds the first summary response open, performs a newer
manual scan and refresh, confirms the new metrics are visible, and then releases
the old response. The dashboard remains on the newer state.
