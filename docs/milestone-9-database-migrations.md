# Milestone 9 — Ordered database migrations

## Purpose

Nova 0.9.0 replaces startup-time additive schema repair with an explicit,
ordered SQLite migration registry. This establishes a stable upgrade boundary
before learning, OCR metadata, or other persisted capabilities add more data.

## Migration guarantees

- Versions are contiguous and applied in ascending order.
- Every version has a stable descriptive name.
- Each migration runs inside a SQLite savepoint.
- A migration is recorded only after its schema work succeeds.
- A failed migration rolls back its own partial changes.
- Re-running initialization is idempotent.
- Existing records survive adoption of the migration registry.
- A database from a newer Nova version is refused rather than downgraded.
- A recorded migration name that differs from this build is treated as
  incompatible history.

Nova retains the earlier `schema_meta` value as a compatibility marker while
`schema_migrations` becomes the authoritative ordered history.

## Legacy adoption

Databases from the earlier MVP already report one broad schema version even
though their tables evolved incrementally. The first migration set therefore
uses idempotent table and index creation plus narrow, explicit legacy-column
checks. It records versions 1 through 8 only after the existing schema has been
brought to the same verified shape as a new database.

This adoption does not delete or rewrite inventory, understanding,
recommendation, approval, or action rows.

## Future rule

Every future change to persisted SQLite structure must add one new migration.
Previously released migrations must not be edited or reordered. Upgrade tests
must begin with the prior schema and prove that user records remain intact.
