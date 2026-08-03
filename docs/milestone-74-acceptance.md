# Milestone 74 - Acceptance Record

**Date:** 3 August 2026

**Release candidate:** 0.74.0

**Status:** Passed; product implementation merged and exact merged-main runtime
verified; evidence-only publication remains

## Automated checks passed

- Backend Ruff passed.
- Backend strict mypy passed for all 34 source files.
- Backend pytest passed 149 of 149 tests.
- Backend coverage passed at 93.30 percent against the 90 percent requirement.
- Frontend ESLint passed.
- Frontend TypeScript passed.
- Frontend Vitest passed 48 of 48 tests.
- Frontend production build passed and its final artifact was moved to
  `N:\Nova\Artifacts\milestone-74\frontend-dist-final`.
- Windows launcher/control structural validation passed.
- Docker Compose configuration validation passed.
- Changed-file whitespace validation passed.

The existing non-failing React `act(...)` warnings remain visible in two
dashboard tests. They predate this backend guidance correction and do not affect
the 48 passing assertions; they remain a low-priority test-harness cleanup item.

## Installed-runtime checks passed

- Backend and frontend containers are running; backend is healthy.
- Local health reports version `0.74.0`.
- Private same-origin health over Tailscale reports version `0.74.0`.
- The active database passed NOVA's read-only SQLite integrity check.
- Docker ports remain bound to Windows loopback.
- Tailscale Serve remains tailnet-only at
  `https://nova.tail1d0293.ts.net`.
- Recent backend and frontend logs contain no matching error, critical,
  traceback, exception, or HTTP 5xx event.
- The post-test backup is verified and its independently recalculated SHA-256
  matches NOVA's recorded value.

## Real local-model checks passed

The installed `qwen3:8b` model was asked the owner's original question through
the production Chat API:

> I'm looking to improve you to assist me to your fullest potential.

The first two synthetic runs were deliberately rejected because they exposed a
contradictory reminder example and then an invented document-citation example.
The guidance was tightened after each finding and all synthetic conversations
were archived rather than deleted.

Final synthetic conversation
`dcadb9f7-28b0-43af-bc4a-9ceac36f91aa` returned HTTP 200, persisted one user
message and one assistant message, checked approved knowledge, and cited no
unsupplied source. Its answer accurately described:

- private local chat;
- approved local knowledge;
- remember review cards and owner approval;
- one explicit document selection for the current turn;
- conversation organisation controls;
- Focus and owner-entered next actions; and
- the absence of web browsing, automatic file access, scheduling, external
  actions, unselected-file access, and autonomous execution.

It ended with supported next steps: share one current goal or preference, ask
NOVA to remember it, or select a document through the interface for that turn.

## Physical-owner acceptance

The owner asked the same capability question in the installed NOVA Chat
interface and confirmed that the corrected answer passed. This verifies that
the response is materially more useful in the real interface, not only through
the synthetic API acceptance path.

## Current release-readiness decision

All automated, installed-runtime, recovery, privacy, architecture, real-model,
physical-owner, protected-check, and exact merged-main checks passed. Product
PR #20 merged with merge commit `4057e071392ad1b2c5686093112040eb0645ebbe`.
Release `0.74.0` is approved; only protected integration of this release
evidence, tag creation, and publication remain.
