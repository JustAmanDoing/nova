# Milestone 57 — Engineering Review

**Review date:** 28 July 2026

**Prototype release:** 0.57.0

**Decision:** Accepted

## Review scope

- deterministic duplicate detection and owner confirmation;
- guarded record updates;
- non-destructive retirement;
- immutable revision and append-only event evidence;
- active-only retrieval;
- verified knowledge snapshots;
- interface behavior and local-action enforcement; and
- regression safety for all existing NOVA functions.

## Automated evidence

- Ruff passed.
- Strict mypy passed for 31 application source files.
- 122 backend tests passed.
- Backend coverage is 92.42%, above the required 90%.
- ESLint passed.
- TypeScript passed.
- 29 frontend tests passed.
- The pinned pnpm 9.15.5 frozen-lock production installation passed.
- The Vite production build passed.
- Backend and frontend production container builds passed.
- Docker Compose configuration validation passed.
- Windows controller structural verification passed.
- `git diff --check` passed.

Focused tests prove:

- exact duplicate proposals are visibly marked;
- approval fails until separate-record confirmation is supplied;
- updates leave the previous file unchanged and retrieve the new revision;
- retirement requires an exact record-specific phrase;
- retired records are excluded from retrieval while files remain present;
- lifecycle mutations without the local-action header are rejected;
- snapshots contain the expected manifest and tracked files;
- snapshot SHA-256 sidecars match;
- archive integrity passes; and
- changed tracked files cause snapshot creation to fail without an archive.

## Engineering assessment

The implementation is bounded, testable, and consistent with existing service
ownership. It uses transactions for database state, no-overwrite file
creation, path containment, and SHA-256 verification. Failure paths leave
earlier knowledge files intact. The owner interface explains duplicate,
revision, retirement, and snapshot behavior before action.

The existing non-failing React `act(...)` warnings in intake dashboard tests
remain. They predate this milestone and do not affect the knowledge lifecycle
test results.

## Live Windows evidence

- The production stack reported version 0.57.0 and healthy services.
- Ports remained loopback-only at `127.0.0.1:8000` and
  `127.0.0.1:5173`.
- Migration 14 was recorded and `PRAGMA integrity_check` returned `ok`.
- A synthetic exact duplicate was marked with the correct active record,
  path, and score 1.0.
- Approval without separate-record confirmation returned HTTP 409. The
  duplicate proposal was then rejected, leaving one record.
- Updating the accepted record created revision 2 at a new path and retained
  the revision 1 file.
- Live retrieval supplied revision 2 and answered `golden comet [K1]`.
- Wrong retirement confirmation returned HTTP 422.
- Correct record-specific confirmation produced retired revision 3 while
  retaining the current file.
- A fresh retrieval omitted the retired record and correctly stated that no
  Milestone 57 acceptance colour was available.
- The verified knowledge snapshot contained the lifecycle record, revisions
  1–3, and both immutable files. All six manifest revision checks matched their
  archived SHA-256.
- Phone-width testing at 390 px found a horizontal-overflow defect in the
  conversation strip. The defect was corrected, rebuilt, and retested with
  `scrollWidth` below the viewport width.
- The final browser showed all lifecycle controls, the retired revision, and
  no console errors.
- The exported post-acceptance database passed independent integrity checking,
  contained migration 14, and retained the retired revision 3 evidence.

## Release-readiness decision

Milestone 57 passes engineering release-readiness. The approved lifecycle scope
works in the production Windows stack, preserves owner control and immutable
evidence, and has verified recovery checkpoints.

## Owner acceptance

The owner tested the installed 0.57.0 prototype and confirmed `passes` on
29 July 2026.

No merge to `main` and no remote push are part of this review.
