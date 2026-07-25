# Milestone 26: Active database integrity guard

## Outcome

Nova now runs SQLite's fast read-only integrity check before applying any
schema migration to the active database.

## Safety behavior

At startup, Nova:

1. opens the configured local database;
2. refuses it immediately if SQLite cannot configure the normal safe
   connection;
3. runs `PRAGMA quick_check`;
4. proceeds with ordered migrations only when SQLite reports `ok`;
5. otherwise stops with guidance to restore a verified backup.

The guard does not attempt automatic repair. A damaged database remains
byte-for-byte unchanged, preserving the best chance of controlled recovery.
Existing backup creation and restore checks remain in place.

## Verification

The database tests cover a valid empty database, existing migration paths, and
an invalid database file. The invalid file is rejected before migration and is
confirmed unchanged afterward.
