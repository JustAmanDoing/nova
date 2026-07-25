# Milestone 21: Validated storage boundaries

## Purpose

Nova scans the intake tree recursively and performs approved moves into a
separate library. A configuration that nests intake, library, backups, or the
database inside one another could create processing loops, inventory noise, or
unsafe recovery assumptions.

## Startup validation

Nova now refuses to start when:

- intake, library, and backup directories are equal or nested;
- the SQLite database is inside any document or backup directory.

Sibling paths remain valid. Paths are resolved before comparison so an existing
symbolic link cannot silently bypass the boundary.

The validation does not create, move, delete, or inspect user files. It fails
before the intake service begins and identifies the conflicting configuration
areas in the startup error.
