# Milestone 35: Resilient Windows readiness

## Outcome

Nova 0.35.0 makes the Windows start and update result more reliable after a
slow first container build. It also preserves the final readiness error when a
deployment genuinely cannot become available.

## Changes

- API, dashboard, and backup probes use `127.0.0.1`, matching the exact
  loopback-only Compose port bindings instead of depending on local hostname
  resolution.
- The readiness window is three minutes. Docker image construction happens
  before this window, so it measures only container startup and service
  availability.
- Every unsuccessful probe records a bounded reason. A final timeout shows that
  reason together with Compose state and the most recent 80 container log
  lines.
- The user-facing dashboard URL remains `http://localhost:5173`.

## Reason

A verified live update to 0.34.0 built and started both containers correctly,
but the 90-second controller window reported a timeout just before the
dashboard became available. The API, dashboard, database, and version were all
healthy immediately afterward. This change addresses the observed Windows
startup timing without weakening health checks.

## Validation

The Windows script check requires explicit IPv4 probe addresses, the
three-minute bound, retained failure detail, bounded logs, and PowerShell syntax
validity. Backend, frontend, and isolated production workflow checks remain
unchanged.
