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
