# Milestone 82 — Minimum timesheet Structured Information Loop

Status: implemented on the construction branch; not merged, installed, or owner-accepted.

## Bounded behavior

NOVA's existing Chat intake recognizes clear timesheet details without requiring the word
`timesheet`. It maintains one open shift record and briefly confirms each saved value. A
normal correction replaces the earlier value and is recorded in the audit history.

Each shift stores its Brisbane date, loading and driving start/finish times, odometer
start/finish values, delivery count, derived total minutes, and individually recorded toll
points. Total hours are derived from loading start through driving finish, including an
overnight finish, and are recalculated after relevant corrections. Date and total hours are
not requested as duplicate owner input.

An end-of-shift request reports only missing required inputs. Tolls are optional for
completeness. A complete shift remains in NOVA's existing SQLite database for retrieval and
weekly use.

## Current toll-price resolution

During a shift, NOVA records only the named toll point. Gateway is normalized to the
official Murarrie toll point, and Kuraby is normalized to Kuraby/Compton Road.

For weekly output, NOVA fetches the current Class 4 heavy-commercial prices from the
[official Linkt/Transurban Brisbane toll-pricing page](https://www.linkt.com.au/using-toll-roads/about-brisbane-toll-roads/toll-pricing/brisbane).
No dollar price table is stored in source code or the database. The official page must
contain all four expected Brisbane toll points; if it is unavailable or its structure no
longer verifies, NOVA reports that the total cannot be calculated and does not guess.

## Architecture and scope

The change adds one timesheet service and one forward-only database migration within the
existing modular monolith. It reuses Chat streaming, capability evidence, the shared SQLite
database, and the shared write lock. It does not change memory or filing behavior and adds
no dashboard, tracking, external account integration, agent, Voice Chat, calendar, payroll,
or invoicing behavior.

## Verification

Automated coverage includes:

- ordinary-chat progressive capture and exact confirmations;
- replacement corrections and recalculated total hours;
- persistence across service instances and retrieval after completion;
- missing-field checking that excludes derived and optional values;
- named toll capture and correction;
- current official Class 4 table parsing, aliases, safe failure, and weekly totals;
- migration preservation of existing approved knowledge;
- a complete HTTP Chat shift without a model provider.

The end-to-end scenario covers progressive values, a toll, a corrected loading start,
derived hours, an incomplete end-of-shift check, completion, saved-record retrieval, and a
weekly toll-dollar result.

Merge, guarded installation, live end-to-end verification, and owner acceptance remain
separate approval gates. Voice Chat remains out of scope and blocked.
