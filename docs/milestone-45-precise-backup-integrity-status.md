# Milestone 45 — Precise Backup Integrity Status

Nova 0.45.0 makes the backup history describe exactly what the lightweight
listing operation has established.

## Behavior

- A retained backup with a syntactically valid SHA-256 sidecar is labelled
  **Checksum recorded**.
- The history summary reports **checksums recorded**, rather than calling every
  listed backup verified.
- A missing or malformed checksum remains **Checksum unavailable** and needs
  attention.
- Download and restore controls remain available only when a valid checksum
  record exists.
- Every download and restore still recalculates the backup SHA-256 value and
  checks SQLite integrity immediately before returning or using the backup.

## Why this matters

The bounded backup inventory reads filenames, file metadata, and checksum
sidecars. It intentionally does not hash and open every retained database once
per minute. Calling that lightweight state “verified” could imply a recent
content and database-integrity check that did not occur during listing.

The new wording keeps the dashboard accurate without adding growing background
disk work. Full verification remains at the safety boundary where it is needed:
download and restore.

## Verification

Frontend tests confirm the checksum-recorded summary, per-backup label, and
integrity-checked download description. Existing backend tests continue to
exercise changed-backup rejection and SQLite integrity checks for download and
restore.
