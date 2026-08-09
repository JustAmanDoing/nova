# Milestone 79 - Librarian Daily-Use Validation

**Validation start:** 9 August 2026

**Validated release:** 0.78.2

**Validated repository base:** `d7615cdfc2238f12d459ed26bcbd6cdcb4b88e3a`

**Status:** In progress; technical PC and phone-sized checkpoint passed, owner
daily-use feedback pending

## Objective

Validate the accepted read-only Librarian during ordinary PC and private-phone
use before proposing any change to its detection rules or authority. This
milestone records evidence only. It adds no runtime behavior, dependency, data,
schema, deployment, network, automatic action, or second review store.

## Live checkpoint

The installed Windows runtime reported healthy NOVA 0.78.2. The active database
passed its integrity check, Docker remained bound to Windows loopback, the
private Tailscale HTTPS route worked, and Funnel remained off.

The direct backend, PC same-origin route, and private phone route returned
equivalent Librarian health, review-queue, and item-detail evidence:

- knowledge health: 100;
- 16 active records and 16 verified sources;
- duplicate, conflict, stale, missing-file, broken-reference, and checksum
  findings: zero; and
- four low-priority optional missing-coverage suggestions, ordered by title:
  Emergency plan, Financial goals, Home responsibilities, and Vehicle context.

Every item exposed a deterministic reason, checklist evidence, confidence,
safe optional next step, and an existing Chat review link. The links prepared
an editable prompt and displayed that nothing had been sent or saved.

## Read-only proof

The live API and UI health refresh, queue reads, all four detail reads, evidence
dialogs, and review handoff were exercised without submitting a prompt.

| State | Result |
| --- | --- |
| Active database SHA-256 | Before and after values matched; the private value was not published |
| Approved-knowledge manifest SHA-256 | Before and after values matched; the private value was not published |
| Approved-knowledge files | All 19 files were unchanged |

No knowledge was edited, merged, retired, deleted, uploaded, inferred, or
added. No automatic action occurred.

## Usability checkpoint

The PC page and a 390 by 844 phone viewport were reviewed against the private
route. The page had no horizontal overflow, retained understandable health and
queue summaries, kept all four issues in the expected order, and exposed the
same evidence and review destinations as the API. The evidence dialog stayed
within the phone viewport; its close and review controls were 44 pixels high.
No browser warning or error was recorded.

Responsive navigation keeps four destinations visible by hiding the current
page's own link. Librarian remained reachable from the other primary pages,
and its own page retained Chat, Focus, Record, and Intake links.

## Verification

- Backend Ruff: passed.
- Backend strict mypy: passed for 40 source files.
- Backend pytest: 164 passed with 93.65% coverage.
- Frontend lint and type check: passed.
- Frontend Vitest: 55 passed, including all three Librarian tests.
- Frontend production build: passed.
- Windows launcher and controller checks: passed.
- Compose configuration: passed.
- Protected GitHub CI on the exact repository base: all required jobs passed.
- Installed runtime, PC route, private route, API equivalence, responsive UI,
  review handoff, and data-preservation checks: passed.

The frontend suite still emits existing non-failing React `act(...)` warnings,
and the local build emits an existing Node `url.parse()` deprecation warning.
Neither warning is specific to the Librarian or changed by this milestone.

## Remaining daily-use evidence

Synthetic responsive checks support acceptance but do not replace physical
owner use. The remaining bounded evidence is whether, during normal phone use:

1. the four optional suggestions are understandable and not distracting;
2. their ordering feels useful;
3. View evidence provides enough explanation; and
4. Review opens the expected editable prompt without unexpected action.

This feedback is required to measure false-positive friction. Do not change a
detection rule merely to make the current queue shorter. The live store also
has no duplicate, conflict, stale, missing-file, broken-reference, or checksum
issue, so those states remain covered by automated tests rather than a
synthetic mutation of owner data.

The private route works, but the existing Windows phone-status control still
cannot prove route ownership because its original Serve ownership record is
absent. The control remains fail-closed and no network setting was changed.

## Current decision

The technical checkpoint passes with no observed runtime, privacy, integrity,
or usability defect. Milestone 79 remains in progress until the owner records
normal phone-use feedback. Release 0.78.2 remains installed and unchanged.

Any approval-assisted Librarian action still requires a new architecture and
engineering decision plus explicit owner approval.

## Exact next action

Use Librarian once from the private phone route and report whether the four
optional items are useful as shown or identify any item that feels noisy,
unclear, or wrongly ordered. Do not add knowledge merely to complete this
validation.
