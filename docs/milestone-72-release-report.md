# Milestone 72 - Release Report

**Report date:** 1 August 2026

**Release:** 0.72.0

**Status:** Release approved; evidence-only protected integration and tag
pending

## Decision

Milestone 72 is safe to release. The implementation, automated verification,
recovery checks, installed-runtime checks, simulated-phone checks, private
network checks, and physical-phone owner acceptance all passed. No
release-blocking defect remains.

This report is the final evidence-only repository change. After its protected
checks pass, merge it with a merge commit, preserve both Milestone 72 branches,
tag that exact `main` commit as `v0.72.0`, publish the GitHub release, and
verify that GitHub `main`, the tag, and the installed health endpoint still
identify release 0.72.0.

## Findings closed

- Long conversations no longer expand the whole phone page or force the owner
  to scroll past the complete transcript before reaching the latest reply.
- Each conversation opens at its latest exchange while retaining chronological
  message order and an explicit **Jump to latest** control.
- **New chat** and a phone **Chats** drawer keep the primary journey within
  reach.
- Rename, Archive, Move to Trash, and Restore are explicit, guarded,
  reversible, and auditable.
- Archive and Trash preserve every message and keep historical conversations
  locally reviewable.
- Permanent deletion remains deliberately outside the approved scope.

## Architecture, safety, and privacy

- The modular monolith remains unchanged.
- The SQLite database remains the authoritative source for conversations,
  messages, and lifecycle events.
- Schema migration 17 preserves existing records and adds only reversible
  lifecycle state plus append-only audit events.
- Every lifecycle mutation uses the existing local owner-intent boundary.
- No message or conversation is permanently deleted or overwritten.
- No external provider, listener, dependency, sync, telemetry, semantic
  search, plugin, or agent was added.
- Docker publications remain bound to Windows loopback only.
- Private phone access remains Tailscale Serve on the owner's tailnet; public
  Funnel remains off.
- No secret, generated dependency tree, build output, cache, database, backup,
  or temporary artifact was added to Git.

## Completed checks

### Implementation and automated verification

- Backend Ruff passed.
- Backend mypy passed for 34 source files.
- Backend pytest passed 148 of 148 tests.
- Backend coverage passed at 93.30 percent against the 90 percent requirement.
- Frontend ESLint and TypeScript passed.
- Frontend Vitest passed 48 of 48 tests.
- Frontend production build passed with output directed to `N:`.
- Docker Compose validation and both production image builds passed.
- Windows controller checks passed.
- Changed-file whitespace, credential-pattern, and prohibited-artifact checks
  passed.

### Protected implementation integration

- Draft implementation PR #18 reviewed commits
  `975162d3ba91ce32b41c86ca0cf9a7e26f9c0ee5` and
  `671f458d47d52097781e1cc54e9dc6cfc92b8aa9`.
- Required Backend quality, Frontend quality, Windows controls, and Production
  runtime checks passed after owner acceptance was recorded.
- PR #18 was marked ready and merged using merge commit
  `2cd5b14d524ad678aecbc3211c0445b56b6ed0d5`.
- The implementation branch
  `agent/milestone-72-conversation-organisation` remains preserved.

### Exact merged runtime

- Exact merged `main` rebuilt both production containers successfully.
- Local and private tailnet HTTPS health returned `ok` and version `0.72.0`.
- Backend and frontend containers are running; backend is healthy.
- Active SQLite schema 17 passed the read-only integrity check.
- Operational status is healthy with no warnings and 96.1 percent free
  storage.
- Knowledge quality reports eight verified active records, 63.3 percent core
  coverage, 100 percent freshness, and eight of eight retrieval checks passed.
- Recent container logs contain no `ERROR`, `CRITICAL`, `Traceback`, or
  `Unhandled` match.
- Tailscale Serve remains tailnet-only at
  `https://nova.tail1d0293.ts.net`; public Funnel remains off.
- Fresh post-merge backup `nova-20260801T005128.425632Z.db` passed API
  verification, checksum-sidecar verification, independent SHA-256
  recalculation, and a read-only SQLite integrity check at schema 17. Its
  SHA-256 is
  `624f0b9895061967ea2e2a036c1f68b8715569eed3a4a92cde7ee9f4512316f7`.

### Owner acceptance

The owner passed the physical-phone workflow. The latest reply and composer
appeared together, **Chats** exposed old-conversation selection and the
guarded lifecycle controls, and closing the drawer returned cleanly to chat.

## Remaining limitations and non-blocking risks

- Existing React asynchronous-test `act(...)` diagnostics remain in dashboard
  tests; they do not fail the suite or affect the accepted chat behavior.
- Knowledge core coverage is intentionally incomplete at 63.3 percent. NOVA
  displays those gaps and does not invent missing information.
- Daily use may reveal naming, archive, Trash, recovery, or list-growth
  friction. Those observations belong to the next evidence-only validation
  milestone, not an unreviewed expansion of this release.

## Release result

Release approved. Protected implementation PR #18 passed and merged. The
evidence-only PR, annotated tag `v0.72.0`, GitHub release, and final alignment
check remain before publication is complete.

## Exact next milestone

**Milestone 73 - Conversation Organisation Daily-Use Validation.** Use normal
phone and PC chat for several days, record evidence about conversation-list
growth and lifecycle usability, and select no new runtime feature from this
milestone. Milestone 73 starts only after release 0.72.0 is published.
