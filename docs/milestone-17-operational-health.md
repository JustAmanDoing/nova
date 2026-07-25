# Milestone 17: Operational health

## Outcome

Nova now reports a small, read-only set of measurements that show whether its
current computer and intake workload have healthy headroom.

## Measurements

The local status endpoint and dashboard show:

- application uptime
- local database size
- total and free space on the drive that contains `data/intake`
- free-space percentage
- latest scan outcome
- latest scan completion time
- latest scan duration

Scan measurements cover automatic startup scans, background scans, and manual
scans. They reset when Nova restarts; no monitoring history or document content
is added to the database.

## Conservative warnings

Nova reports **Needs attention** when:

- the intake drive has less than 5 GB free
- the intake drive has less than 10% free
- the latest scan failed
- the latest scan took longer than 30 seconds
- storage or database size cannot be inspected

A warning is advisory. Nova does not buy, install, move, delete, archive, or
upload anything in response. Hardware or storage recommendations can now be
based on the displayed measurements and real usage.

## Privacy boundary

The endpoint is read-only and returns sizes, timings, state, and safe warning
text. It does not return host paths, filenames, document text, exception
details, hardware identifiers, or network information.
