# Milestone 72 - Acceptance Record

**Date:** 1 August 2026

**Release candidate:** 0.72.0

**Status:** Automated, installed-runtime, and simulated-phone checks passed;
physical-phone owner acceptance pending

## Automated checks passed

- Backend Ruff passed.
- Backend strict mypy passed for the changed source modules.
- Backend pytest passed 148 of 148 tests.
- Backend coverage passed at 93.30 percent against the 90 percent requirement.
- Frontend ESLint passed.
- Frontend TypeScript passed.
- Frontend Vitest passed 48 of 48 tests.
- Frontend production build passed and wrote its artifact to `N:`.
- Docker Compose configuration and both production image builds passed.
- Changed-file whitespace validation passed.

## Migration and recovery checks passed

- A verified, checksum-recorded pre-migration database backup was created on
  `N:` and its SHA-256 was independently recalculated successfully.
- Installed SQLite integrity returned `ok` after migration.
- Installed schema version is 17.
- Existing conversation data remained readable after migration.
- The lifecycle-event table is present and records real guarded transitions.
- A synthetic acceptance conversation completed Rename, Archive, Restore,
  Move to Trash, and Restore without losing its identifier or history. It was
  archived after testing so it does not clutter the active list.

## Phone-size browser checks passed

At an accepted 390 by 844 phone viewport:

- the 79-message conversation opened at its latest exchange;
- the transcript remained bounded at 180 pixels rather than expanding the
  page by the full history;
- the latest message, composer, and Send control were visible together;
- scrolling upward exposed **Jump to latest**, which returned to the final
  exchange;
- **New chat** remained in the sticky header;
- the **Chats** drawer exposed selection, Rename, Archive, Move to Trash,
  archived review, and Restore;
- the drawer stayed within the phone viewport; and
- horizontal page overflow was zero.

## Installed and private-runtime checks passed

- Backend and frontend containers are running; backend is healthy.
- Installed local and private health both report version `0.72.0`.
- Direct local Chat returned HTTP 200.
- Private tailnet Chat returned HTTP 200 over HTTPS.
- Private same-origin health returned `ok`.
- Docker ports remain bound to `127.0.0.1`.
- Tailscale Serve remains tailnet-only at
  `https://nova.tail1d0293.ts.net`.
- Public Funnel remains off.
- Post-install backup `nova-20260731T222503.909102Z.db` is checksum-recorded,
  SQLite-verified, and independently matches SHA-256
  `624f0b9895061967ea2e2a036c1f68b8715569eed3a4a92cde7ee9f4512316f7`.
- Recent backend and frontend logs contain no `ERROR`, `CRITICAL`,
  `Traceback`, or `Unhandled` match.

## Remaining acceptance gate

The owner must perform one physical-phone check: open the private Chat page,
confirm the latest exchange and composer are together, open **Chats**, and
confirm an old conversation can be selected and the guarded management
controls are visible. No destructive action is required.

Until that passes, the candidate must not merge, tag, or publish as release
0.72.0.
