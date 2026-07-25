# Milestone 14 — Windows controls

## Outcome

Nova 0.14.0 can be started, stopped, checked, and safely updated on Windows
without remembering command-line sequences. Four root-level `.cmd` launchers
delegate to one reviewable PowerShell controller.

## Start

**Start Nova.cmd**:

1. Confirms Docker and Compose are installed.
2. Confirms Docker Desktop is running.
3. Builds and starts the Compose project in detached mode.
4. Waits for both the health API and dashboard for up to 90 seconds.
5. Opens `http://localhost:5173` only after Nova is ready.

A failed build or readiness timeout displays direct guidance and leaves Docker
logs available for diagnosis.

## Stop and status

**Stop Nova.cmd** runs ordinary `docker compose down`. It never passes `-v`, so
the named SQLite volume remains intact; document and backup folders also remain
on disk.

**Check Nova.cmd** shows Compose state and checks the versioned health endpoint.
An unavailable dashboard is reported without changing the deployment.

## Guarded update

**Update Nova.cmd** requires both Git and Docker. It refuses to continue when
the worktree has local changes, then uses `git pull --ff-only`. This prevents an
update from silently overwriting local work or creating an unexpected merge.
After a successful fast-forward, it follows the normal build and readiness
flow.

## Validation

`scripts/Test-NovaScripts.ps1` parses the shared controller with PowerShell's
own syntax parser and verifies that all four launchers exist, call that
controller, and request the intended action.

The scripts never install dependencies, delete volumes, alter application data,
or change Nova's network boundary.
