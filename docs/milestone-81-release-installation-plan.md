# Milestone 81 - Release and Guarded Installation Plan

**Prepared:** 12 August 2026

**Integrated product commit:** `d88fd00c950291ff79b5b9922e6dc2d4249ecca6`

**Proposed release:** `v0.81.0`

**Status:** Prepared and independently reviewed in draft PR #45. The backend
package, API-reported version, frontend package, and health endpoint test are
aligned to `0.81.0`. The first preparation CI run exposed one stale `0.80.0`
health-test assertion; it was corrected, and protected run `31552602819` passed
Backend quality, Frontend quality, Windows controls, and Production runtime on
the corrected code and test. The current PR checks remain authoritative after
any later evidence-only edit. This document and its version changes do not
authorize merging the preparation pull request, creating a tag or GitHub
release, changing the Windows installation, or recording owner acceptance.

## Purpose

Milestone 81 adds one shared NOVA application shell around the five workspaces
that already exist: Chat, Focus, Record, Librarian, and Intake. It provides a
persistent desktop navigation rail, a responsive private-phone drawer, and a
Chat workspace that keeps conversation history, transcript, and composer in
separate regions.

The dedicated owner file **Library** workspace is not part of Milestone 81.
Librarian remains knowledge-health guidance. Release 0.81.0 must not imply that
the approved Library workspace has been implemented.

## Release-version decision

`0.81.0` is the proposed version because this is the first release for
Milestone 81 and it changes the primary user interface across the existing
workspaces. The preparation change aligns the backend package, API-reported
version, frontend package version, and health endpoint test to `0.81.0`.

The tag must point to the exact protected-`main` commit produced after the
release-preparation pull request merges. Do not tag the earlier product merge
`d88fd00c950291ff79b5b9922e6dc2d4249ecca6`, because that commit still declares
version `0.80.0`.

## Verified preparation baseline

Before this plan was prepared:

- PR #43 was owner-approved and merged into protected `main` at
  `d88fd00c950291ff79b5b9922e6dc2d4249ecca6`;
- exact-candidate protected CI run `31549576713` passed Backend quality,
  Frontend quality, Windows controls, and Production runtime;
- post-merge protected-`main` run `31550946912` passed the same four jobs;
- the latest published GitHub release remained `v0.80.0`; and
- the authoritative Google Drive `NOVA Handoff` recorded Milestone 81 as
  integrated but unreleased, uninstalled, and not physically accepted.

Preparation verification then established:

- initial PR #45 run `31552463699` passed Frontend quality, Windows controls,
  and Production runtime but correctly failed Backend quality because the
  health endpoint test still expected `0.80.0`;
- commit `78f1aa16d5fcf78caf0ffdd3a9154f70933139e8` aligned that test with the
  proposed release version; and
- protected run `31552602819` then passed Backend quality, Frontend quality,
  Windows controls, and Production runtime.

Any later PR head must receive its own protected checks. The pull request and
GitHub Actions, not this narrative, are authoritative for the final exact-head
result.

## Independent preparation review

The finished preparation diff was reviewed against current protected `main`:

- it changes only three version declarations, one corresponding health test,
  the Milestone 81 evidence, and this release/install plan;
- the backend package, API response, frontend package, and test all agree on
  `0.81.0`;
- it adds no endpoint, schema migration, dependency, provider, agent, plugin,
  data authority, storage boundary, or network exposure;
- neither tag nor GitHub release `v0.81.0` existed at review time;
- the planned installation uses NOVA's existing updater, which rejects local
  changes, creates and validates the pre-update backup before downloading,
  uses `git pull --ff-only`, and performs normal rebuild/readiness checks;
- the plan keeps the release, installation, physical acceptance, and Handoff
  update behind explicit owner authority; and
- no remaining blocking scope, privacy, recovery, versioning, or installation
  issue was found.

## Owner approval bundle

One explicit owner approval may authorize this bounded sequence after all
required checks remain green on the current release-preparation PR head:

1. mark the release-preparation pull request ready and merge it into protected
   `main`;
2. verify all required checks against the exact merged `main` commit;
3. create tag `v0.81.0` and publish the GitHub release from that exact commit;
4. run NOVA's guarded Windows update against the clean real installation;
5. complete the PC and private-phone acceptance checks below; and
6. update and read-after-write verify Google Drive `NOVA Handoff` with the
   release, installation, acceptance, remaining limitations, and next action.

Approval is limited to this exact scope. Stop and return to the owner if the
version, commit, release contents, updater behavior, network boundary, data
state, or acceptance scope differs. The owner's later physical observation
still determines whether acceptance passes; approval to run the checks is not
an advance acceptance result.

## Release notes prepared for review

### NOVA 0.81.0 - Persistent App Shell and Workspaces

NOVA 0.81.0 adds a shared application shell around Chat, Focus, Record,
Librarian, and Intake.

- Desktop receives a persistent workspace navigation rail.
- Private-phone layouts receive a compact header and responsive workspace
  drawer.
- Selecting a workspace shows that workspace rather than stacking unrelated
  features into one page.
- Chat preserves separate conversation-history, transcript, and bottom-composer
  regions.
- The closed mobile drawer cannot receive pointer or keyboard focus, and the
  rail remains scrollable on short displays.

This release adds no backend endpoint, database migration, dependency, external
provider, agent, plugin, storage authority, or network exposure. The dedicated
file Library workspace is not included.

## Preflight before release or installation

Record and reconcile these facts before any tag or live change:

- Google Drive `NOVA Handoff` still names this release and installation bundle
  as the exact next action;
- protected `main`, the preparation pull request, its exact head, and all
  required Actions results agree;
- all three production version declarations and the health test report
  `0.81.0`;
- tag `v0.81.0` and a release with that tag do not already exist;
- the real Windows checkout is on `main`, clean, fetched, and can fast-forward
  to the approved exact release commit;
- the currently installed version and exact source commit are recorded from the
  real checkout and health endpoint rather than inferred from an old tag;
- current Docker health, active-database integrity, backup inventory, available
  storage, private Tailscale Serve state, and Funnel-off state are recorded
  read-only; and
- the current installation remains available until the guarded updater begins.

Stop before publishing or installing if any fact cannot be verified.

## Guarded Windows installation

Use the existing `Update Nova.cmd` / `scripts/Nova.ps1 update` workflow only.
Do not replace it with manual copying, an unreviewed script, a hard reset,
volume deletion, or ad-hoc container recreation.

1. Confirm the real checkout is clean and on `main` at the recorded pre-update
   commit.
2. Keep the running NOVA service available so the updater can request its
   online pre-update backup.
3. Run the guarded updater. It must reject local edits, create and verify a new
   backup before downloading source, use `git pull --ff-only`, rebuild the
   existing production services, and wait for readiness.
4. Record the backup filename, `verified=true` result, SHA-256 value, and
   filename-bound checksum sidecar. Stop if any backup evidence is absent or
   inconsistent.
5. Verify the installed source commit exactly matches tag `v0.81.0` and the
   approved protected-`main` release commit.
6. Verify direct loopback and same-origin health report NOVA `0.81.0`, the
   backend runs unprivileged, the active SQLite database passes the existing
   read-only integrity check, and no unexpected migration occurred.
7. Verify the normal services remain loopback-bound, private Tailscale Serve is
   healthy, and public Funnel remains off.

## PC acceptance

On the real Windows installation, verify:

- the persistent navigation rail is visible at desktop width;
- Chat, Focus, Record, Librarian, and Intake each open their own workspace and
  show the correct active navigation state;
- workspace switching preserves the existing feature behavior and does not
  create a second data or status authority;
- Chat history, transcript, model control, New Chat action, and bottom composer
  remain usable without overlap or horizontal overflow;
- keyboard focus is visible and the navigation rail remains usable on a short
  viewport; and
- browser console and same-origin requests show no release-blocking error.

## Private-phone acceptance

Through the existing private Tailscale address, verify:

- the compact header and workspace button fit the handset without horizontal
  clipping;
- the workspace drawer opens, closes by button/backdrop/Escape where available,
  and hidden drawer links cannot be activated while closed;
- tapping Chat, Focus, Record, Librarian, and Intake opens only the selected
  workspace;
- Chat history remains separate from workspace navigation;
- the transcript scrolls above a usable bottom composer without overlap; and
- the route remains private, with no public Funnel or router-port exposure.

The owner must physically confirm the PC and phone result. Automated browser or
CI evidence supports but does not replace physical acceptance.

## Data-preservation evidence

Before and after installation, record:

- active-database integrity;
- database and relevant local-store counts needed to detect unexpected loss;
- approved-knowledge and Project Record verification summaries where available;
- backup inventory including the new verified pre-update backup; and
- confirmation that no intake, library, knowledge, backup, or Project Record
  file was deleted, overwritten, uploaded, or moved by the release process.

Milestone 81 has no schema migration and should not change domain data. Normal
local Chat history created during acceptance is the only expected user-data
write.

## Stop and rollback boundary

Stop immediately and preserve evidence if:

- the approved version or commit differs;
- the checkout is dirty or cannot fast-forward;
- the pre-update backup is missing, unverified, or has inconsistent checksum
  evidence;
- build, readiness, health, database-integrity, version, or security checks fail;
- private Serve changes unexpectedly or Funnel is enabled;
- navigation hides or mixes workspace content incorrectly;
- Chat controls overlap or become unusable on the PC or phone; or
- any unexpected domain-data mutation or loss is detected.

Record the exact pre-update source commit and verified backup before the update.
Because this milestone has no migration, preserve the current database and do
not restore or delete it merely to roll back the frontend. Do not improvise a
downgrade with `git reset`, delete Docker volumes, or run an older source tree
against unverified state. Any rollback must use the recorded pre-update commit
and NOVA's guarded recovery controls under explicit owner approval.

## Completion gate

Milestone 81 is complete only after all of the following are proven:

- the release-preparation pull request is merged;
- tag and GitHub release `v0.81.0` identify the exact approved protected-`main`
  commit;
- guarded Windows installation succeeds with a verified pre-update backup;
- PC and private-phone acceptance pass;
- data, integrity, loopback, private-Serve, and Funnel-off evidence pass;
- the owner accepts the installed result; and
- Google Drive `NOVA Handoff` is updated and read back successfully.

## Exact next action

Confirm all required protected checks remain green on the current PR #45 head,
then present one explicit owner approval request covering the preparation merge,
verification of merged `main`, `v0.81.0` publication, guarded Windows
installation, and physical PC/private-phone acceptance. Do not execute any of
those actions before that approval.
