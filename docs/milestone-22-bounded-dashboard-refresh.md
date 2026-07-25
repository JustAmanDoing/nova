# Milestone 22: Bounded dashboard refresh

## Purpose

The dashboard needs to show background intake changes without allowing a slow
machine, large scan, or hidden browser tab to create overlapping request
batches.

## Behavior

Nova now schedules the next dashboard refresh only after the current batch has
finished. It pauses refresh work while the page is hidden and aborts outstanding
requests when the view changes or closes.

This preserves the five-second foreground update interval while keeping at most
one automatic dashboard request batch active. Manual actions still refresh the
dashboard immediately after they finish.

From Nova 0.43.0 onward, the growing backup directory inventory is included in
the first batch and then at most once per minute. Live intake, review, action,
recovery, learning, and operational state retain the five-second cadence.
Manual actions still request a complete refresh.

From Nova 0.44.0 onward, every batch receives an increasing local request
identifier. Only the newest batch may update dashboard state or show a loading
error. A slower earlier response is discarded if a later manual or automatic
refresh has already started.
