# NOVA Active Engineering Status

> This is NOVA's one canonical active project-status record. Read it from the
> `project-status` branch on GitHub before making status claims or starting an
> engineering session. Repository, pull-request, CI, release, and verified
> runtime evidence override this summary. Chat memory and packaged project files
> are not current-status sources.

---
record_version: 1
verification: VERIFIED
verified_at: 2026-08-11T10:35:36+10:00
current_milestone: Milestone 80 - implementation and release evidence plan merged; release, installation, and acceptance pending explicit operational approval
integrated_branch: main
integrated_commit: e4e647e1085f37ede172bd7a498e74efbcc7280c
active_branch: main
active_commit: e4e647e1085f37ede172bd7a498e74efbcc7280c
pull_request: none
release: v0.78.2
installed_commit: 93daa9806590c950c94044e637a44125f5739ec0
---

## Verification state

**CURRENT STATUS VERIFIED** on 11 August 2026 (Australia/Brisbane).

Verified against the GitHub repository, draft PR #38 and its exact-head
protected Actions run, plus the actual Windows checkout at
`N:\Nova\Source\nova`.

If this record, its named refs, or required GitHub evidence cannot be read and
reconciled, stop and report **CURRENT STATUS NOT VERIFIED**. Do not guess and do
not begin feature work.

## Current milestone

Milestone 80 bounded Conductor Phase 1 implementation and its release and
installation evidence plan are merged into `main`. Release, guarded Windows
installation, and physical PC/private-phone acceptance are not started or
approved. The merged plan does not change NOVA runtime behavior.

## Completed work

- Milestone 79 Librarian daily-use validation and Knowledge Examples Phase 1
  are merged, installed as NOVA 0.78.2, technically verified, and
  owner-accepted on PC and phone.
- Milestone 80 capability, architecture, engineering, risk, test, and rollout
  reviews were approved for the bounded four-request implementation.
- The candidate implements four exact read-only Conductor status requests,
  no-model routing for those requests, evidence persistence, Migration 18, UI
  starters and evidence cards, regression coverage, and CI smoke coverage.
- The canonical GitHub status branch, mandatory repository instructions,
  engineering workflow, live fail-closed resume check, and Windows structural
  regression guard are merged into `main` through PR #39. Milestone 80 product
  work remains paused pending an explicit next direction.
- PR #40 adds the Milestone 80 release and installation evidence plan.
  It defines the explicit approval bundle, existing guarded updater path,
  no-destructive rollback boundary, runtime/security/data-preservation proof,
  and PC/private-phone acceptance evidence required before completion.

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

For continuity commit `f8be9d7121881643790c6292803960ba45c7b1c7`:

- `git diff --check` passed.
- PowerShell syntax validation passed.
- `scripts/Test-NovaScripts.ps1` passed with the continuity regression guard.
- The live GitHub resume check reconciled `main`, the Milestone 80 head, and
  draft PR #38.
- A deliberately missing status ref failed closed with
  `CURRENT STATUS NOT VERIFIED`.
- Draft PR #39 protected CI passed on the exact continuity commit: Windows
  controls, Backend quality, Frontend quality, and Production runtime.
- PR #39 was merged into `main` at
  `0a4d66a8c9abe4a1421ab3ac9c6b316bf8d45fe7` after explicit owner approval.
- PR #38 was rebased onto current `main` without conflicts. The refreshed head
  passed GitHub Actions run 31444210954: Windows controls, Backend quality,
  Frontend quality, and Production runtime.
- An independent final review of the refreshed PR #38 diff found no blocking
  scope, privacy, authority, migration, recovery, dependency, or regression
  issue. It confirmed four exact normalized read-only routes, fixed local
  evidence links, additive evidence persistence, bounded output, and truthful
  failure behavior. The review did not authorize merge, release, installation,
  or physical acceptance.
- PR #38 was marked ready and merged into `main` after explicit owner approval
  at `2ea7b1d85f343029bda5e0cd39c908a209aff524`.
- For draft PR #40 commit `9d9a37449f5e9c171e739b25021cfc6e1c0a8b08`, the
  canonical GitHub resume check passed before work, `git diff --check` passed,
  and every linked local control/path in the new plan was verified present.
  GitHub Actions run 31446577504 passed: Windows controls, Backend quality,
  Frontend quality, and Production runtime all completed successfully before
  the plan merged.

## Branch and commit

- Integrated branch: `main`
- Integrated `main` commit: `e4e647e1085f37ede172bd7a498e74efbcc7280c`
  (includes the Milestone 80 implementation merge
  `2ea7b1d85f343029bda5e0cd39c908a209aff524` and the plan merge)
- Active branch and commit: `main` at
  `e4e647e1085f37ede172bd7a498e74efbcc7280c`
- Actual Windows checkout: clean `agent/fix-knowledge-gap-refresh` at
  `b3bd610cbd0536fd99c26001d1211b47d92dee0a`; after fetch, that local branch is
  behind its remote by four commits. Its local `main` remains stale at
  `29e6b092077db672a7cdd36bb691b3afc0d25c4e` and must not be used for current
  status.

## Pull request and release state

- PR #39, **Establish GitHub-backed engineering continuity**, merged into
  `main` at `0a4d66a8c9abe4a1421ab3ac9c6b316bf8d45fe7`; all four protected CI jobs
  passed before merge.
- PR #38, **Add bounded Conductor status routing**, merged into `main` at
  `2ea7b1d85f343029bda5e0cd39c908a209aff524` after all four refreshed
  protected checks and explicit owner approval.
- PR #40, **Add Milestone 80 release evidence plan**, passed all four protected
  checks and was merged into `main` after explicit owner approval at
  `e4e647e1085f37ede172bd7a498e74efbcc7280c`.
- No Milestone 80 release, Windows installation, or physical acceptance is
  approved.
- Current installed release: NOVA 0.78.2 at installed commit
  `93daa9806590c950c94044e637a44125f5739ec0`.
- Release tag `v0.78.2` resolves to repository commit
  `0dcb6f34869ee595286e56fcc9a04b091e0e4716`; later accepted installation and
  documentation commits are recorded above.
- No NOVA 0.80.0 release exists in the verified evidence.

## Blockers and risks

- The continuity workflow is operational and integrated. The actual Windows
  checkout remains clean but stale on an older branch and must be aligned
  deliberately before local feature engineering resumes.
- The GitHub App remains read-only for mutations, but GitHub CLI authentication
  is restored with repository and workflow scopes. The continuity read path
  remains public and read-only, so it does not depend on that credential.
- Release publication, guarded Windows installation, exact merged-main runtime
  verification, physical PC/private-phone acceptance, and release evidence
  remain outstanding. Passing CI and the independent review do not replace
  those gates.
- Physical PC/private-phone acceptance, guarded installation, release evidence,
  release/tag approval, and owner installation approval remain outstanding.

## Exact next action

Explicitly approve or adjust the operational bundle defined by the merged plan:
tag/publish the exact approved Milestone 80 commit/version if still correct,
run the guarded Windows update, and perform PC/private-phone acceptance. Do
not begin that work until this separate approval is explicit.

## Session closeout requirement

At the end of every NOVA work session, replace the active facts in this file in
one focused `project-status` branch commit and push it to GitHub. Preserve these
sections: current milestone, completed work, checks and tests, branch and
commit, pull request and release state, blockers and risks, and exact next
action. Do not preserve a claim that current evidence disproves.
