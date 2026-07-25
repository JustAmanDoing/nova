# Milestone 31: Full runtime workflow verification

## Outcome

Nova's production-container verification now exercises the guarded intake
workflow beyond read-only observation. It proves the deployed services can
complete and reverse a real file action, preserve its audit record, and recover
the live database from a verified backup.

## Isolated scenario

GitHub Actions creates one synthetic invoice and then:

1. waits for local extraction and a deterministic recommendation
2. approves the current recommendation through the guarded local API
3. executes the separately confirmed no-overwrite move
4. verifies the filed copy and append-only successful action
5. undoes the move and verifies the source is restored
6. creates and checks a verified SQLite backup
7. restores that exact backup with the required confirmation phrase
8. confirms the automatic safety backup and healthy API

The scenario runs only in the disposable CI checkout and Docker volume. The
workflow always removes its containers and database volume, even after failure.

## Boundaries preserved

- No real user file, database, backup, secret, or Docker volume is available.
- Every state-changing request carries Nova's local-action intent header.
- Approval and execution remain separate requests.
- The move and undo retain no-overwrite and SHA-256 verification.
- Restore still requires a verified checksum and exact per-file confirmation.
- No automatic filing behavior is introduced.

## Verification

The existing unit and integration suites continue covering failure paths. The
production job adds an end-to-end proof using the built Python and Nginx
containers, host bind mounts, loopback ports, live HTTP API, and real SQLite
volume.
