# Milestone 39: Early storage capacity planning

## Outcome

Nova 0.39.0 reports limited storage headroom before the drive reaches a
failure-prone state. The local dashboard and Windows status controller now use
the same read-only operational measurements and advisory warnings.

## Warning levels

Nova reports:

- an early capacity-planning warning when both less than 25 GB and less than
  20% of the intake drive remain;
- the existing low-storage warning when less than 5 GB or less than 10%
  remains.

The combined early threshold avoids advising an upgrade merely because a large
drive is below 20% while it still has substantial absolute capacity.

## Windows visibility

**Check Nova.cmd** now prints:

- free storage in GB and percent;
- each safe operational warning returned by Nova;
- a clear healthy message when no warning exists.

The same information is printed after a successful start or update, so limited
headroom is visible without opening the dashboard's System health panel.

## Safety boundary

These checks are read-only. Nova does not prune Docker caches, remove images,
delete backups, move documents, purchase hardware, or alter storage in response
to a warning. Cleanup and hardware changes remain explicit user decisions.
