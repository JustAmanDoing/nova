# Milestone 24: Reproducible Python dependencies

## Purpose

Nova's frontend uses a lockfile, but the backend previously resolved the newest
package allowed by each broad compatibility range on every installation. That
could make two builds from the same commit behave differently.

## Constraint contract

`backend/constraints.txt` records the exact Python dependency set verified on
both Windows and Linux. The production image and backend CI job install through
that file while `pyproject.toml` remains the declaration of supported direct
dependency ranges.

This separates two concerns:

- `pyproject.toml` describes which package families Nova supports;
- `constraints.txt` makes a particular Nova build repeatable.

Dependency updates must change the declaration and constraints together, run
the full backend checks on Windows and Linux, and pass the production-container
smoke test before merging.
