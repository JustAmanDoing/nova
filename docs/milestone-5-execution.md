# Milestone 5 — Guarded Execution, Audit, and Undo

## Outcome

Nova can move an approved file from `data/intake` into its reviewed destination
under `data/library`. Approval and execution remain separate user actions. No
background scan, recommendation, or approval can execute a move.

## Execution preconditions

Every move rechecks all of the following:

1. The inventory file and deterministic recommendation still exist.
2. The file is not an exact duplicate.
3. The recommendation is current for the source fingerprint and intake status.
4. The matching review status is `approved`.
5. The reviewed filename and destination remain valid Windows-safe relative
   paths.
6. The resolved source remains inside the intake root.
7. The resolved destination remains inside the library root.
8. The destination does not exist.
9. A fresh SHA-256 fingerprint still matches the reviewed source.

Any failed check stops the operation without changing the source.

## Verified move

Nova creates the destination with exclusive-create semantics, so an existing
file cannot be overwritten. It copies the content, flushes it to disk, verifies
the destination SHA-256, re-verifies the source SHA-256, and only then removes
the source. If copying or verification fails while the source still exists,
Nova removes the incomplete destination where possible.

## Append-only audit

The `action_events` table stores immutable events. Every operation receives a
stable operation ID and records:

- Move or undo
- Started, succeeded, or failed state
- Source and destination relative paths
- SHA-256 fingerprint
- Related move operation for undo
- Safe plain-language detail
- Timestamp

The API presents the latest state of each operation while retaining every
underlying event.

## Undo

Undo is available only for a successful move that has not already been undone.
Nova requires the filed copy to match the recorded fingerprint and requires the
original intake path to be empty. Undo then uses the same exclusive,
copy-verify-remove sequence in reverse and records a separate operation.

## Recovery posture

The append-only `started` event is committed before the filesystem operation.
If the process stops unexpectedly, the audit retains evidence of the
interrupted operation. Nova does not guess or silently resolve an interrupted
move. The no-overwrite and verify-before-remove rules prefer recoverable extra
copies over data loss.

## Explicit non-goals

- No automatic filing
- No overwrite
- No permanent deletion
- No bulk execution
- No learning or confidence-threshold automation
- No chatbot or cloud AI dependency
