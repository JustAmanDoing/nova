# Milestone 48 — Independent dashboard resources

## Outcome

Nova now refreshes each dashboard data source independently. A temporary
failure in one optional or secondary panel no longer blocks fresh results from
the rest of the intake workflow.

## Behaviour

- File inventory, summary totals, action history, recovery assessments, backup
  history, learning preferences, and operational status settle independently.
- Successful requests update their own dashboard state immediately.
- A failed request preserves that resource's last known data instead of
  replacing it with an empty result.
- Partial failures are combined into one accessible alert with the affected
  resource named explicitly.
- A failed file-list request is represented as unavailable and is not
  misreported as a genuinely empty intake.
- An optional panel failure does not hide the truthful empty-intake state when
  the file request itself succeeds with no files.

## Concurrency and retry guarantees

The existing latest-request-wins guard remains in place. Results from an older
manual or automatic refresh cannot overwrite newer dashboard state.

The bounded backup refresh checkpoint also remains precise: Nova advances the
minute checkpoint only when the backup inventory request succeeds. A failed
backup request is therefore retried on the next five-second foreground cycle.

## Verification

Frontend tests cover:

- fresh intake files remaining visible when operational status fails;
- a truthful empty-intake state remaining visible when learning preferences
  fail;
- scoped partial-failure diagnostics;
- prompt retry after a failed backup refresh; and
- suppression of stale overlapping request results.

This change stays within the existing single-page architecture and introduces
no new service or persistence layer.
