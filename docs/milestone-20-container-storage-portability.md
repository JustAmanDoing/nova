# Milestone 20: Container storage portability

## Purpose

Nova's application runs without root privileges, but host bind mounts can use
different ownership on Windows, Linux, and hosted CI runners. The production
container must be able to initialize its own storage folders without leaving
the application running as root.

## Boundary

At container startup a small entrypoint runs with the minimum elevated
privilege needed to:

1. create `/data`, `/files/intake`, `/files/library`, and `/files/backups`;
2. assign only those Nova-owned directories to the `nova` account; and
3. immediately replace itself with the API process running as `nova`.

The entrypoint does not recursively change document ownership, inspect file
contents, or broaden filesystem permissions. Existing intake documents only
need to be readable by the application.

## Verification

The repository includes structural tests for the privilege-drop and path
contract. GitHub Actions performs the decisive runtime check by building the
production images, starting the real Compose stack against a fresh bind mount,
and confirming that the API, dashboard, and intake scanner become healthy.
