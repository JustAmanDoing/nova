# Milestone 33: Runtime version guard

## Outcome

Nova 0.33.0 makes a stale local deployment visible instead of reporting only
that its containers are healthy. The Windows controller compares the version
declared by the current source checkout with the version returned by the
running API.

## Behaviour

- **Start Nova.cmd** verifies the running API version after the rebuilt
  dashboard and API become ready. A mismatch stops the launch flow with a
  direct explanation.
- **Check Nova.cmd** continues to report a healthy application, but highlights
  any version mismatch and directs the user to rebuild with **Start Nova.cmd**.
- The version is read from `backend/pyproject.toml`, which remains aligned with
  the backend health response and frontend package version.

The guard is read-only. It does not pull source, restart containers, or change
application data.

## Validation

The Windows launcher check now:

- parses the controller with PowerShell's own parser;
- requires both version-checking functions and recovery guidance;
- verifies that the backend package, API default, and frontend package versions
  match.

The normal production workflow still proves that a freshly built container
returns the expected version through its health endpoint.
