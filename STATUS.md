# NOVA Active Engineering Status

> This is NOVA's one canonical active project-status record. Read it from the
> `project-status` branch on GitHub before making status claims or starting an
> engineering session. Repository, pull-request, CI, release, and verified
> runtime evidence override this summary. Chat memory and packaged project files
> are not current-status sources.

---
record_version: 1
verification: VERIFIED
verified_at: 2026-08-10T13:45:00+10:00
current_milestone: Milestone 80 - Conductor Phase 1 candidate in progress; feature work paused for continuity
integrated_branch: main
integrated_commit: 1905e442699d923c2ea6a70b62e17712684f330b
active_branch: agent/milestone-80-conductor-phase-1
active_commit: bce194bbe3154ce1ec2c895d779a55cbaa72d43c
pull_request: 38
release: v0.78.2
installed_commit: 93daa9806590c950c94044e637a44125f5739ec0
---

## Verification state

**CURRENT STATUS VERIFIED** on 10 August 2026 (Australia/Brisbane).

Verified against the GitHub repository, draft PR #38 and its exact-head
protected Actions run, plus the actual Windows checkout at
`N:\Nova\Source\nova`.

If this record, its named refs, or required GitHub evidence cannot be read and
reconciled, stop and report **CURRENT STATUS NOT VERIFIED**. Do not guess and do
not begin feature work.

## Current milestone

Milestone 80 is in progress. Its bounded Conductor Phase 1 implementation is a
candidate only. It is not merged, released, installed, or owner-accepted.
Milestone 79 is complete and integrated on `main`.

## Completed work

- Milestone 79 Librarian daily-use validation and Knowledge Examples Phase 1
  are merged, installed as NOVA 0.78.2, technically verified, and
  owner-accepted on PC and phone.
- Milestone 80 capability, architecture, engineering, risk, test, and rollout
  reviews were approved for the bounded four-request implementation.
- The candidate implements four exact read-only Conductor status requests,
  no-model routing for those requests, evidence persistence, Migration 18, UI
  starters and evidence cards, regression coverage, and CI smoke coverage.
- Further Milestone 80 product work is paused until the engineering-continuity
  workflow is committed and verified.

## Checks and tests

For Milestone 80 candidate commit
`bce194bbe3154ce1ec2c895d779a55cbaa72d43c`:

- Backend Ruff and strict mypy passed; 169 backend tests passed with 93.56%
  coverage.
- Frontend lint and typecheck passed; 58 tests and the production build passed.
- Windows controls, Compose validation, both production image builds,
  repository checks, and an isolated no-model Conductor smoke passed.
- GitHub Actions run 31341779982 completed successfully. Windows controls,
  Backend quality, Frontend quality, and Production runtime all passed.
- Existing non-failing React `act(...)` warnings remain.

## Branch and commit

- Integrated branch: `main`
- Integrated commit: `1905e442699d923c2ea6a70b62e17712684f330b`
- Active feature branch: `agent/milestone-80-conductor-phase-1`
- Active feature commit: `bce194bbe3154ce1ec2c895d779a55cbaa72d43c`
- Actual Windows checkout: clean `agent/fix-knowledge-gap-refresh` at
  `b3bd610cbd0536fd99c26001d1211b47d92dee0a`; after fetch, that local branch is
  behind its remote by four commits. Its local `main` remains stale at
  `29e6b092077db672a7cdd36bb691b3afc0d25c4e` and must not be used for current
  status.

## Pull request and release state

- Draft PR #38, **Add bounded Conductor status routing**, is open and mergeable
  against `main`.
- PR #38 protected CI is successful.
- Merge, release, Windows installation, and physical acceptance are not
  approved.
- Current installed release: NOVA 0.78.2 at installed commit
  `93daa9806590c950c94044e637a44125f5739ec0`.
- Release tag `v0.78.2` resolves to repository commit
  `0dcb6f34869ee595286e56fcc9a04b091e0e4716`; later accepted installation and
  documentation commits are recorded above.
- No NOVA 0.80.0 release exists in the verified evidence.

## Blockers and risks

- Engineering continuity must be committed and verified before more Milestone
  80 implementation or merge consideration.
- The actual Windows checkout is clean but stale and on an older branch; align
  it deliberately before local feature engineering resumes.
- Local GitHub CLI authentication reports an invalid token. The continuity read
  path therefore uses GitHub's public read-only API and does not require that
  credential.
- PR #38 documentation and description still say protected CI is required even
  though the exact-head run passed. Correct that evidence only after continuity
  is operational.
- Physical PC/private-phone acceptance, guarded installation, release evidence,
  owner merge approval, and owner installation approval remain outstanding.

## Exact next action

Implement and verify the engineering-continuity workflow on the dedicated
`agent/engineering-continuity` branch, without changing Milestone 80 product
code. Then update this record to the continuity commit and PR state.

## Session closeout requirement

At the end of every NOVA work session, replace the active facts in this file in
one focused `project-status` branch commit and push it to GitHub. Preserve these
sections: current milestone, completed work, checks and tests, branch and
commit, pull request and release state, blockers and risks, and exact next
action. Do not preserve a claim that current evidence disproves.
