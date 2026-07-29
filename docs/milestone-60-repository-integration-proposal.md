# Milestone 60 Proposal — Repository Integration and Protected Main

**Proposal date:** 29 July 2026

**Proposed base:** accepted Milestone 59 release 0.59.0

**Working branch:** `agent/milestone-59-guided-knowledge-onboarding`

**Draft pull request:** <https://github.com/JustAmanDoing/nova/pull/1>

**Status:** Approved by the owner; release gate and exact-head verification
remain mandatory

## Purpose

Milestones 53 through 59 are accepted on the local working branch and the
installed Windows prototype is healthy. GitHub `main` still represents the
pre-Milestone-53 baseline. Milestone 60 should make GitHub a trustworthy
release baseline, then align the installed 0.59.0 runtime with that exact
verified source without changing its accepted data or architecture.

This is repository integration work, not a product-feature milestone.

## Verified starting state

- Accepted local release: `0.59.0`.
- Milestone 59 owner-accepted runtime checkpoint:
  `3aa42a8a3ffd2731f67561dd95761b22ebe192c5`.
- Remote `main`:
  `210a39f88dc0acadb9ec2e12d0c4d4e8053cf687`.
- Remote `main` is an ancestor of the accepted branch head.
- Draft pull request 1 is the cumulative Milestones 53–59 integration request.
- Pull-request head, scope, mergeability, and checks are live release-gate
  evidence. They must be obtained from GitHub immediately before integration
  rather than copied from an earlier proposal snapshot.
- The installed API reports `0.59.0` and both services remain loopback-bound.
- The final accepted database and knowledge checkpoints exist and their
  SHA-256 hashes match the Milestone 59 record.
- `main` currently has no branch protection or repository ruleset.

## Bounded scope

### 1. Exact-head integration gate

- Recheck that pull request 1 still targets `main`.
- Recheck that its head is the approved commit.
- Require every existing Continuous verification job to pass on that exact
  head.
- Refuse integration if the head changes, a check is missing, or the pull
  request is no longer cleanly mergeable.
- Preserve the accepted database and knowledge checkpoints unchanged.
- Review every changed file and stop for any security, privacy, documentation,
  dependency, generated-artifact, or release-evidence defect.

### 2. Protected `main`

Before integration, configure a narrowly scoped rule for `main` that:

- requires the four existing Continuous verification checks;
- blocks force pushes;
- blocks branch deletion;
- does not require an external reviewer that a single-owner repository cannot
  provide; and
- preserves merge commits so the accepted milestone history remains visible.

The owner approved the bounded integration operation on 29 July 2026. The
created rule must be recorded exactly in the final release report.

### 3. Guarded merge

After the release gate passes on the exact pull-request head:

- move the pull request out of draft;
- merge with a merge commit;
- preserve the remote feature branch initially;
- do not squash or rewrite the accepted milestone commits; and
- record the resulting merge commit.

### 4. Post-merge verification

- Confirm remote `main` contains the accepted branch head in its ancestry.
- Confirm the four checks pass for the resulting `main` commit.
- Align the working copy at `N:\Nova\Source\nova` with remote `main` using
  normal Git operations that preserve the feature-branch reference.
- Confirm the N-drive working tree is clean and tracks `origin/main`.
- Create and verify a fresh local recovery checkpoint.
- Use the existing guarded Windows update path to rebuild and restart the
  installed 0.59.0 runtime from the verified merge source.
- Confirm the aligned runtime is healthy, loopback-bound, and still reports
  0.59.0 without changing accepted database or knowledge contents.
- Create annotated tag `v0.59.0` on the verified merge commit and publish a
  GitHub release titled `Release 0.59.0`.
- Confirm the tag and GitHub release target the verified merge commit.
- Update the project status with the merge commit and exact next milestone.

## Explicit exclusions

- No product or runtime feature changes.
- No database migration.
- No Docker rebuild or restart before the merge and post-merge source gate.
- No runtime change beyond the one guarded rebuild needed to align the
  installed 0.59.0 release with the verified merge source.
- No change to the accepted database or knowledge files.
- No deletion of the feature branch.
- No deletion of the old C-drive checkout.
- No version bump beyond the already accepted release `0.59.0`.
- No Milestone 61 runtime work.
- No merge if any release-gate defect or exact-head check remains unresolved.

## Acceptance criteria

1. The pull request head and all four checks are bound to one recorded SHA.
2. The accepted backup files exist and match their recorded SHA-256 values.
3. A main-branch rule prevents force pushes and deletion and requires the
   existing verification suite without locking out the sole owner.
4. Pull request 1 is merged only after explicit owner approval.
5. The merge preserves the full milestone commit history.
6. Remote `main` contains the accepted branch head.
7. Continuous verification passes on the integrated `main`.
8. The N-drive working copy is clean and tracks the integrated `main`.
9. The installed local prototype is rebuilt from verified `main`, remains
   release 0.59.0, and is healthy.
10. No user database or knowledge contents are changed; a new verified recovery
    checkpoint may be created as release evidence.
11. Annotated tag `v0.59.0` and GitHub release `Release 0.59.0` target the
    verified merge commit.

## Rollback and recovery

The existing accepted branch and checkpoints remain intact. The remote feature
branch is retained until post-merge verification is complete. If integration
reveals a repository-only defect, correction occurs through a new guarded
revert or follow-up pull request; history is not rewritten.

The running local prototype is independent of the GitHub merge. A repository
integration failure therefore does not require restoring the database,
knowledge snapshot, or Docker services.

## Recommendation

Execute Milestone 60 as an approved integration-only operation. Use a merge commit,
retain the feature branch through verification, and add a narrow `main` rule
before merging. Do not begin another runtime feature until GitHub and the
N-drive working copy both identify the accepted 0.59.0 source as their
authoritative baseline.

## Current completion estimate

- Guarded Intake MVP: 100%.
- Practical local NOVA prototype: approximately 99%.
- Broader long-term NOVA vision: approximately 75%.
- Milestone 60 implementation: release-gate correction and verification in
  progress.

## Exact next decision

Complete the independent release gate on the exact corrected pull-request head.
If and only if it passes, configure `main` protection, mark pull request 1
ready, merge with a merge commit while preserving the feature branch, verify
the integrated `main`, and publish `v0.59.0`.
