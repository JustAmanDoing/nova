# Milestone 34: Verified pre-update backup

## Outcome

Nova 0.34.0 reduces upgrade risk by creating a verified SQLite snapshot before
the Windows updater downloads source changes whenever the current Nova service
is running.

## Update sequence

After confirming that the Git checkout has no local changes,
**Update Nova.cmd**:

1. checks whether the current health endpoint is available;
2. requests an online backup through Nova's local-only guarded API;
3. requires the returned backup to be verified and to include both a filename
   and SHA-256 fingerprint;
4. stops before `git pull` if a running Nova service cannot create that backup;
5. downloads the fast-forward update and follows the normal build, readiness,
   and version-verification flow.

The backup uses SQLite's online backup mechanism, integrity checking, atomic
publication, and checksum sidecar already established by the backup service.
It remains in the host-mounted `data/backups` folder and is never committed.

## Stopped application

If Nova is not running, the controller cannot request an online backup. It
reports that clearly and continues the update without changing or deleting
existing backups. Users who want the automatic snapshot should start Nova
before running the updater.

## Validation

The Windows control check verifies the API path, local-action intent header,
verified result requirements, and that the backup call occurs before
`git pull`. The production CI workflow independently exercises online backup,
checksum verification, guarded restore, and database integrity.
