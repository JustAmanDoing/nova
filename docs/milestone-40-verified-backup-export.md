# Milestone 40 — Verified Backup Export

Nova 0.40.0 closes a recovery gap between creating a local database backup and
preserving an independent copy.

## Behavior

- The dashboard offers **Download** and **Checksum** only when a backup has a
  valid SHA-256 checksum sidecar.
- The backend rechecks the checksum and SQLite integrity before returning
  either file.
- A missing checksum, changed backup, corrupt database, unsafe name, or missing
  file is refused instead of being exported.
- The response is an attachment with the original constrained backup filename
  and Nova's existing private `no-store` cache policy.
- Download is read-only. It does not create, restore, delete, or alter a backup.

## Recovery guidance

Downloaded backups may contain extracted document text, recommendations,
reviews, and audit history. Keep them private. Preserve the database and its
checksum sidecar together on a different trusted drive so loss of Nova's local
data folder does not remove every recovery point.

Nova does not choose, mount, or write to an external drive automatically. The
user remains in control of the browser's download destination.

## Verification

Backend tests cover valid database and checksum attachments, filenames and
media headers, missing-checksum rejection, changed-backup rejection, and
traversal-safe missing-file handling. Frontend tests confirm that both verified
download actions have file-specific accessible names.
