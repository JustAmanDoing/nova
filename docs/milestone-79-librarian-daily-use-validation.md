# Milestone 79 - Librarian Daily-Use Validation

**Validation start:** 9 August 2026

**Validated release:** 0.78.2

**Initial validation base:** `d7615cdfc2238f12d459ed26bcbd6cdcb4b88e3a`

**Installed current head:** `93daa9806590c950c94044e637a44125f5739ec0`

**Status:** Complete; installed behavior and Knowledge Examples Phase 1 are
technically verified, owner-accepted on PC and phone, and integrated through
PR #33 at merge commit `41adbfff8c0bc44b091ff977e7635abc82e399ce`

## Objective

Validate the accepted read-only Librarian during ordinary PC and private-phone
use before proposing any change to its detection rules or authority. The
milestone began as evidence-only validation. Owner feedback led to the
separately approved copy-only correction in PR #34. It added no detection,
dependency, data, schema, network, automatic action, or second review store.
The later, separately approved Knowledge Examples Phase 1 in PR #35 added
static blank-page guidance without changing those boundaries.

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
  Home jobs and routines, Money goals, and Vehicle details and maintenance.

Every item used everyday wording, explained why it appeared, offered a safe
optional next step, and linked to the existing Chat review flow. Missing checks
also offered two optional examples. The links prepared an editable prompt and
displayed that nothing had been sent or saved.

## Read-only proof

The live API and UI health refresh, queue reads, all four detail reads, evidence
dialogs, and review handoff were exercised without submitting a prompt.

| State | Result |
| --- | --- |
| Active database SHA-256 | Before and after values matched the acceptance record |
| Approved-knowledge manifest SHA-256 | Before and after values matched the acceptance record |
| Approved-knowledge files | All 19 files were unchanged |

No knowledge was edited, merged, retired, deleted, uploaded, inferred, or
added. No automatic action occurred.

Before each guarded installation, NOVA created a verified database backup. The
latest installation backup and preservation hashes are recorded in
`docs/milestone-79-knowledge-examples-acceptance.md`. After installation, the
active database passed its integrity check, all 19 approved knowledge files
remained present, and the same records, sources, and review-item IDs remained
available. Opening the installed Librarian and Chat handoff did not change the
active database.

## Usability checkpoint

The installed PC page and a 390 by 844 phone viewport were reviewed during the
plain-language correction. The exact Knowledge Examples candidate repeated the
responsive review before merge, and the installed private route remained
healthy afterward. The page used the approved labels, kept all four suggestions
in the expected order, and showed the same details as the private route. The
Home jobs and routines explanation and examples fitted within the phone
viewport, every visible example and generic handoff met the 44-pixel touch
target, and the Chat handoff prepared the expected editable sentence. No
browser warning or error was recorded. The owner then accepted the installed
behavior on the physical PC and phone.

Responsive navigation keeps four destinations visible by hiding the current
page's own link. Librarian remained reachable from the other primary pages,
and its own page retained Chat, Focus, Record, and Intake links.

## Verification

- Backend Ruff: passed.
- Backend strict mypy: passed for 40 source files.
- Backend pytest: 165 passed with 93.68% coverage for the current behavior.
- Frontend lint and type check: passed.
- Frontend Vitest: 57 passed for the current behavior.
- Frontend production build: passed.
- Windows launcher and controller checks: passed.
- Compose configuration: passed.
- Protected GitHub CI on the exact repository base: all required jobs passed.
- PR #34 protected CI and post-merge `main` CI: all four jobs passed.
- PR #35 protected CI: all four jobs passed on the exact candidate.
- Windows installation reached merge commit
  `93daa9806590c950c94044e637a44125f5739ec0` after creating a verified backup.
- Installed runtime, PC route, private route, API equivalence, responsive UI,
  review handoff, and data-preservation checks: passed.

The frontend suite still emits existing non-failing React `act(...)` warnings.
They are not specific to the Librarian and were not changed by this milestone.

## Daily-use outcome

Automated responsive checks supported but did not replace physical owner use.
The owner accepted that the installed behavior:

1. makes Home jobs and routines, Money goals, and Vehicle details and
   maintenance understandable;
2. makes it clear that every suggestion is optional;
3. gives enough explanation under Why this is here; and
4. opens the expected editable prompt without unexpected action.

The live store still has no duplicate, conflict, stale, missing-file,
broken-reference, or checksum issue, so those states remain covered by
automated tests rather than a synthetic mutation of owner data. Do not change a
detection rule merely to make the current queue shorter.

## Owner feedback checkpoint

On 9 August 2026, the owner confirmed that the Emergency plan suggestion is not
needed. The owner also confirmed that home responsibilities are useful but the
old technical wording was hard to understand. The owner approved PR #34's
plain-language correction and approved its Windows installation.

After PR #35 renamed the check to Home jobs and routines and added optional
examples, the owner accepted the installed result on both the physical PC and
phone. That acceptance did not add the example sentence to knowledge; permanent
knowledge still requires the existing explicit approval flow.

No emergency-plan knowledge was added merely to clear the queue, and no
detection rule was changed from this single observation. Emergency contacts or
plan remains an optional suggestion that can be ignored. A future Ignore action
or detection change remains a separate product decision.

The private route works, but the existing Windows phone-status control still
cannot prove route ownership because its original Serve ownership record is
absent. The control remains fail-closed and no network setting was changed.

## Current decision

The installed correction and Knowledge Examples Phase 1 pass with no observed
runtime, privacy, integrity, data-preservation, or usability defect. The
installed behavior is owner-accepted and its consolidated validation evidence
is integrated. Milestone 79 is complete. NOVA 0.78.2 remains the installed
version at merge commit
`93daa9806590c950c94044e637a44125f5739ec0`.

Any approval-assisted Librarian action still requires a new architecture and
engineering decision plus explicit owner approval.

## Completion estimate

- Accepted practical local NOVA prototype: 100 percent.
- Broader long-term NOVA vision: approximately 86 percent, unchanged because
  this milestone validates existing behavior rather than adding capability.
- Milestone 79: 100 percent; the behavior and evidence are merged, installed,
  technically verified, and owner-accepted.

## Exact next action

Begin a separate evidence-led capability discussion. No Milestone 80 runtime
scope is approved before architecture review, engineering review, and explicit
owner approval.
