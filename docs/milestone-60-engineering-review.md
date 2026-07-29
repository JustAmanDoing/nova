# Milestone 60 — Engineering Review

**Review date:** 29 July 2026

**Accepted runtime release:** 0.59.0

**Decision:** Conditional release recommendation; owner approval is recorded,
but merge remains blocked until the corrected exact head passes every check

## Review scope

- repository ancestry and working-tree state;
- pull request target, head, draft state, and mergeability;
- exact-head Continuous verification evidence;
- accepted recovery checkpoints;
- installed runtime health and exposure;
- current branch-protection state; and
- proposed integration and rollback controls.

## Verified evidence

### Repository

- N-drive repository:
  `N:\Nova\Source\nova`.
- Working branch:
  `agent/milestone-59-guided-knowledge-onboarding`.
- Milestone 59 owner-accepted runtime checkpoint:
  `3aa42a8a3ffd2731f67561dd95761b22ebe192c5`.
- Remote `main`:
  `210a39f88dc0acadb9ec2e12d0c4d4e8053cf687`.
- Git confirms remote `main` is an ancestor of the accepted head.

### Pull request

- Pull request: 1.
- State: open draft.
- Merge state: clean.
- Target: `main`.
- Source: `agent/milestone-59-guided-knowledge-onboarding`.
- Scope, head, and mergeability are live release-gate evidence and must be read
  directly from GitHub immediately before integration.
- No reviews or unresolved review comments are recorded.

### Continuous verification

The Milestone 59 checkpoint passed the existing GitHub Actions matrix. That
historical result is not sufficient evidence for a later pull-request head.
The corrected release head must independently pass:

- Backend quality.
- Frontend quality.
- Windows controls.
- Production runtime.

The workflow is configured for pull requests and pushes to `main`, uses
read-only repository permissions, and pins external actions to full commits.

### Recovery checkpoints

Both accepted Milestone 59 checkpoints exist and match their recorded hashes:

- Database:
  `nova-20260729T094338.115509Z.db`
- SHA-256:
  `025dca5a2c02a66b566c9cd3b61f219bd5fda78afb03d29ba2d33c8b9221b9ec`
- Knowledge snapshot:
  `nova-knowledge-20260729T094338.326237Z.zip`
- SHA-256:
  `c3bfc4e4dab9a981068caba7f93f0d76f80a25f1242640b912eadd39194a9942`

### Installed runtime

- API health: healthy.
- Reported version: 0.59.0.
- Backend: running and healthy on `127.0.0.1:8000`.
- Frontend: running on `127.0.0.1:5173`.
- Compose working directory: `N:\Nova\Source\nova`.

### GitHub governance

- `main` is not protected.
- No repository ruleset is configured.

## Engineering judgement

The automated matrix is broad enough to support repository integration after
one verified gap is closed: the production-runtime job must assert that the
backend image contains the patched packaging toolchain used by the release
image. The other missing control is enforcement: GitHub does not currently
require the checks or protect `main` from destructive history changes.

A merge commit is preferred over squash or rebase because the milestone
commits are individually meaningful evidence records. Keeping the feature
branch through post-merge verification provides a simple recovery reference.

## Independent release-gate findings

The independent Milestone 60 review identified and bounded these corrections:

1. remove unsupported WEBP guidance from the intake interface and lock the
   supported-format wording with a regression test;
2. upgrade production-image pip to `26.1.2` and assert that exact version in
   the production-runtime workflow;
3. replace stale embedded pull-request counts and check-run identifiers with
   live exact-head requirements;
4. extend the architecture record through the implemented Milestones 57–59
   knowledge lifecycle, quality, and guided-onboarding behavior;
5. replace personal-name values in public test and acceptance fixtures with an
   explicit synthetic identity;
6. correct the Milestone 53 contrast evidence to 6.22:1 against the immediate
   panel background;
7. align Milestone 60 with the owner-authorized `v0.59.0` tag and GitHub
   release; and
8. distinguish already implemented conversational knowledge from broader
   future project and document memory.

None of these corrections changes the database schema, local-first boundary,
owner-approval model, modular-monolith structure, or accepted personal data.
The release gate must be repeated after the correction commit.

## Local correction validation

The correction worktree passed the following local checks before publication:

- Ruff: passed.
- Mypy strict mode: 31 source files, no issues.
- Pytest: 128 tests passed with 92.80% coverage.
- ESLint and TypeScript type checking: passed.
- Vitest: 34 tests passed.
- Vite production build: passed.
- Frontend dependency audit: 0 known advisories across 320 dependencies.
- Windows controller and launcher structural checks: passed.
- Compose configuration and both production image builds: passed.
- Backend image: `nova-api` 0.59.0 with pip 26.1.2.
- Exact production Python package audit: no known vulnerabilities.
- Repository hygiene and secret-shaped content checks: passed.
- Local Markdown links: all 74 resolved.
- Git whitespace validation: passed.

These local results do not replace the required GitHub Actions evidence on the
published correction commit.

## Required pre-merge recheck

Documentation-only commits can change the pull request head without changing
the accepted runtime source. Before any merge:

1. record the exact current pull request head from GitHub;
2. wait for all four checks on that head;
3. confirm clean mergeability;
4. confirm accepted checkpoint hashes again; and
5. confirm the approved branch rule and merge action remain exactly bounded;
6. audit the production image for known dependency vulnerabilities; and
7. recheck every changed path for accidental files, generated artifacts,
   secrets, debug code, and temporary data.

## Remaining limitations

- The cumulative change has not been merged into remote `main`.
- `main` has no protection.
- No post-merge `main` workflow evidence exists.
- The exact merge head must be obtained from GitHub immediately before the
  approval action rather than embedded self-referentially in this document.
- The old C-drive checkout may remain open in another Codex task and is outside
  this milestone.

No engineering blocker exists in the bounded correction design. The owner has
approved the guarded integration sequence, but merge remains prohibited until
the corrected exact head, production image, recovery evidence, and complete
changed-file review all pass.
