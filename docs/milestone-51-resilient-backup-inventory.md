# Milestone 51: Resilient backup inventory

Nova's backup directory is local and may also be inspected or copied by the
user. A backup can therefore disappear after directory discovery but before
Nova finishes reading its metadata. Previously, that narrow race could fail the
whole backup-history request and temporarily hide every remaining recovery
point.

## Change

- Backup records are assembled individually before sorting.
- A file that disappears during that inventory pass is skipped.
- Other valid backup records remain visible and usable.
- Permission, storage, and unexpected read failures are not broadly hidden.
- Backup creation, checksum validation, verified download, and restore behavior
  are unchanged.

## Verification

The backup service test suite removes one discovered backup during checksum
inspection and confirms that the other recovery point remains listed. Existing
tests continue to cover backup creation, checksum handling, verified downloads,
restore confirmation, rollback, and safe API errors.
