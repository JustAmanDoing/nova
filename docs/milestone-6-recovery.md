# Milestone 6 — Interrupted-operation diagnostics

## Purpose

Nova's verified move sequence records a `started` event before touching the
filesystem and a terminal event afterward. A process, machine, or storage
interruption can occur between those events. Version 0.6.0 makes that condition
visible without guessing what happened or changing either file.

## Safety delay

An operation is assessed only when its latest event remains `started` beyond
`NOVA_ACTION_STALE_SECONDS`. The default is 300 seconds. This avoids reporting a
large but still-active copy as interrupted during normal dashboard polling.

## Read-only assessment

For each incomplete operation, Nova:

1. Maps move and undo paths to their correct managed roots.
2. Rejects absolute, parent-traversal, and escaped paths.
3. Checks whether the source and destination are regular files.
4. Calculates SHA-256 only for files that exist and are readable.
5. Compares the current fingerprints with the immutable action event.
6. Returns one of the states below.

| State | Meaning |
| --- | --- |
| `ready_to_retry` | Verified source exists and destination is empty. |
| `completed_without_audit` | Source is absent and verified destination exists. |
| `copy_incomplete` | Verified copies exist at both paths. |
| `conflict` | A path is occupied unexpectedly or content does not match. |
| `missing` | Neither recorded file exists. |
| `unsafe_path` | A recorded path is outside the managed roots. |
| `unreadable` | Storage or permissions prevented inspection. |

## Deliberate boundary

The recovery endpoint and dashboard are diagnostic only. They do not retry,
delete, move, overwrite, or write a replacement audit event. An explicit
reconciliation workflow should be introduced only after representative
interruption cases have been tested and the safe user choices are understood.
