# NOVA Active Engineering Status

> This is NOVA's one canonical active project-status record. Read it from the
> `project-status` branch on GitHub before making status claims or starting an
> engineering session. Repository, pull-request, CI, release, and verified
> runtime evidence override this summary. Chat memory and packaged project files
> are not current-status sources.

---
record_version: 1
verification: VERIFIED
verified_at: 2026-08-11T11:23:00+10:00
current_milestone: Milestone 80 released and installed; mobile Chat layout fix under draft review
integrated_branch: main
integrated_commit: e4e647e1085f37ede172bd7a498e74efbcc7280c
active_branch: agent/fix-mobile-chat-layout
active_commit: f76ee252a1566945b3900d7791b33d1de9eec605
pull_request: 41
release: v0.80.0
installed_commit: e4e647e1085f37ede172bd7a498e74efbcc7280c
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

Milestone 80 bounded Conductor Phase 1 is released as NOVA 0.80.0 and installed
from `main`. The guarded Windows update, local PC endpoint acceptance, and
private Tailscale route acceptance passed. Physical handset UI observation and
owner acceptance have not been captured in this session, so the milestone is
not yet marked complete.

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
- Release `v0.80.0` was published from `main` commit
  `e4e647e1085f37ede172bd7a498e74efbcc7280c`.
- The actual Windows checkout was safely switched from its stale clean branch
  to `main`, then NOVA's existing backup-first, fast-forward-only updater
  installed that exact commit. The updater created verified backup
  `nova-20260811T004350.018805Z.db` with SHA-256
  `016389d51c9c1976583186d80249fc834d809e961edc4b5e8754ba09a001b432`.
- Four exact no-model status requests passed through both the loopback PC API
  and NOVA's private Tailscale route. Each stored one bounded assistant result
  with a source title, generated time, and 64-character SHA-256 evidence that
  survived a conversation reload. No-model unmatched request returned 503;
  database integrity passed after acceptance.
- Draft PR #41 fixes the reported phone overflow: the Chat screen now keeps
  only Nova, Chats, and New chat in its mobile header, hides desktop page links
  at that breakpoint, and corrects invalid mobile width expressions.

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
- Post-install health reported NOVA 0.80.0. The Windows checkout is clean at
  `e4e647e1085f37ede172bd7a498e74efbcc7280c` and exactly matches tag `v0.80.0`.
  Docker rebuilt both services; the backend was healthy and the dashboard was
  ready. The active database passed read-only integrity before and after the
  update and acceptance.
- Private Tailscale Serve remained healthy at NOVA 0.80.0 and Funnel remained
  off. The four capabilities passed on both `127.0.0.1` and the private HTTPS
  route. The local model service was online; an unmatched no-model request
  correctly returned 503. A selected-document no-model probe was rejected by
  request validation with 422 before model execution, so it is recorded as a
  limitation rather than a successful unavailable-model test.
- For draft PR #41 commit `f76ee252a1566945b3900d7791b33d1de9eec605`,
  `git diff --check` passed and `docker compose build frontend` passed using
  NOVA's pinned production TypeScript and Vite build. Local lint/test commands
  were unavailable because this dedicated worktree has no host `node_modules`.
  GitHub Actions run 31449109902 passed: Windows controls, Backend quality,
  Frontend quality, and Production runtime all completed successfully.

## Branch and commit

- Integrated branch: `main`
- Integrated `main` commit: `e4e647e1085f37ede172bd7a498e74efbcc7280c`
  (includes the Milestone 80 implementation merge
  `2ea7b1d85f343029bda5e0cd39c908a209aff524` and the plan merge)
- Active branch and commit: `main` at
  `e4e647e1085f37ede172bd7a498e74efbcc7280c`
- Active review branch and commit: `agent/fix-mobile-chat-layout` at
  `f76ee252a1566945b3900d7791b33d1de9eec605`
- Actual Windows checkout: clean `main` at
  `e4e647e1085f37ede172bd7a498e74efbcc7280c`.

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
- PR #41, **Fix mobile Chat layout**, is open as a draft on
  `agent/fix-mobile-chat-layout` at
  `f76ee252a1566945b3900d7791b33d1de9eec605`; all four protected checks passed.
- Release `v0.80.0`, **NOVA 0.80.0 — Bounded Conductor status routing**, is
  published from `e4e647e1085f37ede172bd7a498e74efbcc7280c`:
  https://github.com/JustAmanDoing/nova/releases/tag/v0.80.0
- Current installed release: NOVA 0.80.0 at
  `e4e647e1085f37ede172bd7a498e74efbcc7280c`.

## Blockers and risks

- The continuity workflow is operational and integrated. The actual Windows
  checkout is clean and aligned to the released `main` commit.
- The GitHub App remains read-only for mutations, but GitHub CLI authentication
  is restored with repository and workflow scopes. The continuity read path
  remains public and read-only, so it does not depend on that credential.
- Physical handset UI observation, owner acceptance, and a separate Milestone
  80 release report remain outstanding. The private route was exercised from
  the PC but no physical phone screenshot or owner-observed UI evidence was
  captured in this session.
- The no-model document-context acceptance probe returned 422 validation before
  model execution rather than the expected 503. This does not authorize a
  behavioral conclusion about the unavailable-model document path.
- PR #41 must pass protected checks, receive owner merge approval, and be
  installed through the guarded updater before the phone layout is changed live.

## Exact next action

Review draft PR #41. After its checks pass, explicitly approve or adjust its
merge and guarded update; then confirm the focused Chat header on the physical
private phone before recording final Milestone 80 owner acceptance.

## Session closeout requirement

At the end of every NOVA work session, replace the active facts in this file in
one focused `project-status` branch commit and push it to GitHub. Preserve these
sections: current milestone, completed work, checks and tests, branch and
commit, pull request and release state, blockers and risks, and exact next
action. Do not preserve a claim that current evidence disproves.
