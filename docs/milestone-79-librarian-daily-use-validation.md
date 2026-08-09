# Milestone 79 - Librarian Daily-Use Validation

**Validation start:** 9 August 2026

**Validated release:** 0.78.2

**Initial validation base:** `d7615cdfc2238f12d459ed26bcbd6cdcb4b88e3a`

**Installed correction head:** `d60799dc56ebc10174076e9b98fb3659b7075fd6`

**Status:** In progress; the approved plain-language correction is installed,
all technical checks passed, and physical owner acceptance is pending

## Objective

Validate the accepted read-only Librarian during ordinary PC and private-phone
use before proposing any change to its detection rules or authority. The
milestone began as evidence-only validation. Owner feedback led to the
separately approved copy-only correction in PR #34. It added no detection,
dependency, data, schema, network, automatic action, or second review store.

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
- four optional suggestions, ordered by title: Emergency contacts or plan,
  Home jobs and projects, Money goals, and Vehicle details and maintenance.

Every item used everyday wording, explained why it appeared, offered a safe
optional next step, and linked to the existing Chat review flow. The links
prepared an editable prompt and displayed that nothing had been sent or saved.

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

Before installation, NOVA created a verified database backup. After the
installation, the backup passed the protected download verification, the active
database passed its integrity check, all 19 approved knowledge files remained
present, and the same 16 active records, verified sources, and review-item IDs
remained available. Opening the installed Librarian and Chat handoff did not
change the active database.

## Usability checkpoint

The installed PC page and a 390 by 844 phone viewport were reviewed. The page
had no horizontal overflow, used the approved plain-language labels, kept all
four suggestions in the expected order, and showed the same details as the
private phone route. The Home jobs and projects explanation fitted within the
phone viewport, every visible control met the 44-pixel touch target, and the
Chat handoff prepared the expected editable sentence. No browser warning or
error was recorded.

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
- PR #34 protected CI and post-merge `main` CI: all four jobs passed.
- Windows installation reached merge commit
  `d60799dc56ebc10174076e9b98fb3659b7075fd6` after creating a verified backup.
- Installed runtime, PC route, private route, API equivalence, responsive UI,
  review handoff, and data-preservation checks: passed.

The frontend suite still emits existing non-failing React `act(...)` warnings,
and the local build emits an existing Node `url.parse()` deprecation warning.
Neither warning is specific to the Librarian or changed by this milestone.

## Remaining daily-use evidence

Automated responsive checks support acceptance but do not replace physical
owner use. The remaining bounded evidence is whether the installed wording:

1. makes Home jobs and projects, Money goals, and Vehicle details and
   maintenance understandable;
2. makes it clear that every suggestion is optional;
3. gives enough explanation under Why this is here; and
4. opens the expected editable prompt without unexpected action.

This feedback is required to measure false-positive friction. Do not change a
detection rule merely to make the current queue shorter. The live store also
has no duplicate, conflict, stale, missing-file, broken-reference, or checksum
issue, so those states remain covered by automated tests rather than a
synthetic mutation of owner data.

## Owner feedback checkpoint

On 9 August 2026, the owner confirmed that the Emergency plan suggestion is not
needed. The owner also confirmed that home responsibilities are useful but the
old technical wording was hard to understand. The owner approved PR #34's
plain-language correction and approved its Windows installation.

No emergency-plan knowledge was added merely to clear the queue, and no
detection rule was changed from this single observation. Emergency contacts or
plan remains an optional suggestion that can be ignored. A future Ignore action
or detection change remains a separate product decision.

The private route works, but the existing Windows phone-status control still
cannot prove route ownership because its original Serve ownership record is
absent. The control remains fail-closed and no network setting was changed.

## Current decision

The installed correction passes with no observed runtime, privacy, integrity,
data-preservation, or automated usability defect. Milestone 79 remains in
progress only until the owner physically accepts the installed wording. NOVA
0.78.2 remains the installed version at repository head
`d60799dc56ebc10174076e9b98fb3659b7075fd6`.

Any approval-assisted Librarian action still requires a new architecture and
engineering decision plus explicit owner approval.

## Completion estimate

- Accepted practical local NOVA prototype: 100 percent.
- Broader long-term NOVA vision: approximately 86 percent, unchanged because
  this milestone validates existing behavior rather than adding capability.
- Milestone 79: approximately 95 percent; the correction is merged, installed,
  and technically verified, with physical owner acceptance still pending.

## Exact next action

Open the installed Librarian page on the phone or PC and report whether the new
wording is clear. In particular, check Home jobs and projects, Why this is here,
and Open. Do not add knowledge merely to complete this validation.
