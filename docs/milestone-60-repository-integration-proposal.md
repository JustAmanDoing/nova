# Milestone 60 Proposal — Repository Integration and Protected Main

**Proposal date:** 29 July 2026

**Proposed base:** accepted Milestone 59 release 0.59.0

**Working branch:** `agent/milestone-59-guided-knowledge-onboarding`

**Draft pull request:** <https://github.com/JustAmanDoing/nova/pull/1>

**Status:** Proposed; remote changes and merge require explicit owner approval

## Purpose

Milestones 53 through 59 are accepted on the local working branch and the
installed Windows prototype is healthy. GitHub `main` still represents the
pre-Milestone-53 baseline. Milestone 60 should make GitHub a trustworthy
release baseline without changing the accepted runtime.

This is repository integration work, not a product-feature milestone.

## Verified starting state

- Accepted local release: `0.59.0`.
- Accepted branch head:
  `3aa42a8a3ffd2731f67561dd95761b22ebe192c5`.
- Remote `main`:
  `210a39f88dc0acadb9ec2e12d0c4d4e8053cf687`.
- Remote `main` is an ancestor of the accepted branch head.
- Draft pull request 1 is open and GitHub reports it as cleanly mergeable.
- The pull request contains 14 intentional commits across Milestones 53–59.
- Continuous verification run `30442222388` passed on the exact accepted head.
- Backend quality, frontend quality, Windows controls, and production runtime
  all passed.
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

### 2. Protected `main`

Before integration, configure a narrowly scoped rule for `main` that:

- requires the four existing Continuous verification checks;
- blocks force pushes;
- blocks branch deletion;
- does not require an external reviewer that a single-owner repository cannot
  provide; and
- preserves merge commits so the accepted milestone history remains visible.

The exact remote rule must be shown to the owner before it is created.

### 3. Guarded merge

After explicit owner approval:

- move the pull request out of draft;
- merge with a merge commit;
- preserve the remote feature branch initially;
- do not squash or rewrite the 14 accepted milestone commits; and
- record the resulting merge commit.

### 4. Post-merge verification

- Confirm remote `main` contains the accepted branch head in its ancestry.
- Confirm the four checks pass for the resulting `main` commit.
- Align the working copy at `N:\Nova\Source\nova` with remote `main` using
  normal Git operations that preserve the feature-branch reference.
- Confirm the N-drive working tree is clean and tracks `origin/main`.
- Confirm the already installed 0.59.0 runtime remains healthy.
- Update the project status with the merge commit and exact next milestone.

## Explicit exclusions

- No product or runtime feature changes.
- No database migration.
- No Docker rebuild, restart, or reinstall merely to integrate Git history.
- No change to the accepted database or knowledge files.
- No deletion of the feature branch.
- No deletion of the old C-drive checkout.
- No GitHub release, tag, or version bump.
- No Milestone 61 runtime work.
- No merge or branch-rule mutation without explicit owner approval.

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
9. The installed local prototype remains release 0.59.0 and healthy.
10. No user data, knowledge, backups, or runtime service is changed.

## Rollback and recovery

The existing accepted branch and checkpoints remain intact. The remote feature
branch is retained until post-merge verification is complete. If integration
reveals a repository-only defect, correction occurs through a new guarded
revert or follow-up pull request; history is not rewritten.

The running local prototype is independent of the GitHub merge. A repository
integration failure therefore does not require restoring the database,
knowledge snapshot, or Docker services.

## Recommendation

Approve Milestone 60 as an integration-only operation. Use a merge commit,
retain the feature branch through verification, and add a narrow `main` rule
before merging. Do not begin another runtime feature until GitHub and the
N-drive working copy both identify the accepted 0.59.0 source as their
authoritative baseline.

## Current completion estimate

- Guarded Intake MVP: 100%.
- Practical local NOVA prototype: approximately 99%.
- Broader long-term NOVA vision: approximately 75%.
- Milestone 60 implementation: not started; proposal and reviews only.

## Exact next decision

The owner must explicitly approve or reject:

> Configure the proposed `main` protection, mark pull request 1 ready, and
> merge it with a merge commit while preserving the feature branch.

