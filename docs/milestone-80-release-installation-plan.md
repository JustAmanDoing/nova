# Milestone 80 - Release and Installation Evidence Plan

**Prepared:** 11 August 2026

**Merged implementation:** `2ea7b1d85f343029bda5e0cd39c908a209aff524`

**Status:** Plan only. It does not authorize a tag, GitHub release, Windows
installation, Tailscale change, or owner acceptance.

## Purpose

Milestone 80 adds four bounded, read-only Conductor status requests to Chat.
Before calling the milestone released or complete, NOVA must prove the exact
merged source works in the guarded Windows environment and on the private phone
route without expanding authority or changing owner data unexpectedly.

## Approval gate

The owner must explicitly approve the following bundle before it begins:

1. tag and publish the exact merged `main` commit as the approved 0.80.0
   release, if the proposed release version remains correct;
2. run the guarded Windows update on the real NOVA checkout; and
3. perform the listed PC and private-phone acceptance checks.

Do not infer this approval from the PR merge. Do not install a different commit,
release a different version, or combine this work with another product change.

## Preflight evidence

Record these facts before any tag or installation:

- canonical status is verified from `project-status/STATUS.md`;
- `main` resolves to
  `2ea7b1d85f343029bda5e0cd39c908a209aff524` and the release candidate has no
  local modification;
- the proposed tag/version, exact commit, PR #38 merge, and all four protected
  check results are reconciled;
- the real Windows checkout is fetched and shown clean before `Update Nova.cmd`
  runs; and
- the existing installed version, active database integrity, backup inventory,
  Docker health, private Serve state, and Funnel-off state are recorded without
  changing them.

PR checks prove their candidate only. Run the normal merged-main build/runtime
verification before release evidence is accepted.

## Guarded installation procedure

After approval, use NOVA's existing `Update Nova.cmd` workflow. Do not replace
it with a manual file copy, volume recreation, reset, or destructive cleanup.

1. Confirm the checkout is clean and aligned with the approved exact commit.
2. Keep the current NOVA service running so the updater can request its online
   pre-update backup.
3. Record the backup filename, `verified=true` result, and independently
   checked SHA-256 sidecar. Stop if the guarded backup fails.
4. Let the updater fast-forward only, rebuild the existing production images,
   recreate the normal services, and complete its readiness checks.
5. Record the installed version and exact source commit from local and
   same-origin health endpoints. Verify the active SQLite database with the
   existing read-only integrity control.
6. Confirm the backend runs unprivileged, published services remain loopback
   bound, private Tailscale access still works, and Funnel remains off.

## Milestone 80 acceptance evidence

On the installed PC and private-phone route, verify each published starter:

- **Open next actions** returns only current open actions, is bounded, and links
  to Focus.
- **Projects and goals** returns verified planning records only, is bounded, and
  links to Focus.
- **Librarian review** returns the current local health/review summary and links
  to Librarian.
- **NOVA project status** returns the current Project Record summary and links
  to Project Record.

For each result, confirm the visible source title, check time, and truncated
SHA-256 evidence survive a conversation reload. With Ollama unavailable, the
four exact requests must still work; an ordinary unmatched message and a
document-context turn must remain model-gated. The acceptance checks must not
create a next action, alter knowledge, modify Project Record sources, or perform
any domain write other than the expected local Chat history/evidence record.

Capture before/after SQLite integrity and relevant table/count evidence, the
approved-knowledge manifest hash, Project Record verification summary, browser
console result, and PC/phone screenshots or equivalent owner-observed evidence.

## Rollback and stop conditions

Stop and preserve evidence if the approved commit/version differs, the guarded
backup is absent or unverified, migration 18 fails, health/integrity/security
checks fail, private access changes, Funnel is enabled, a status request is not
bounded/read-only, or any acceptance check unexpectedly changes domain data.

Migration 18 is additive. If application rollback is necessary, restore the
verified pre-update database backup through NOVA's guarded restore process;
do not run an older build against the newer database schema. Do not delete
volumes, backups, knowledge, or Project Record sources as part of rollback.

## Release evidence and completion gate

After successful installation and acceptance, record a separate release report
with the exact tag, release URL, merge commit, backup checksum, merged-main and
installed runtime checks, network/security results, data-preservation evidence,
owner acceptance, remaining limitations, and rollback evidence. Only then may
Milestone 80 be marked complete.

## Exact next action

Review this plan and explicitly approve or adjust the tag, guarded installation,
and PC/private-phone acceptance bundle. Until then, do not publish a release or
change the live NOVA installation.
