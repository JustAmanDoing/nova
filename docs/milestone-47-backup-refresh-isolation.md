# Milestone 47 — Isolated Backup Refresh Failure

Nova 0.47.0 keeps the core dashboard current when only the optional backup
inventory request fails.

## Behavior

- Intake files, metrics, action history, recovery assessments, learning
  preferences, and operational status load as one core dashboard group.
- Backup history loads alongside that group but no longer prevents a successful
  core result from being displayed.
- A backup-only failure preserves the last known backup list and shows a clear
  **Backup history** error.
- The failed backup request remains eligible for the prompt retry introduced in
  Nova 0.46.0.
- Core request failures still preserve the last known core state and display
  the underlying safe error message.
- Latest-request-wins ordering and abort handling apply to both result groups.

## Why this matters

Backup history changes slowly and is operationally useful, but it is not
required to review current intake files. Treating every dashboard request as
all-or-nothing allowed a temporary backup-directory or API problem to hide
otherwise fresh intake state.

This isolation keeps the primary workflow useful while making the partial
failure visible and recoverable.

## Verification

The frontend suite forces backup history to fail while returning updated core
metrics. It confirms that the new metric value is rendered and the scoped
backup-history error is announced.
