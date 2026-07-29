# Milestone 63 Engineering Review

**Date:** 30 July 2026

**Release candidate:** 0.63.0

**Decision:** Pass; protected-main CI and Windows acceptance completed

## Implemented

- Safe `GET /api/v1/chat/documents` metadata selector.
- Optional `document_id` on the guarded chat send request.
- Pre-persistence path, readiness, source-hash, current-hash, and byte-limit
  validation.
- Untrusted `[D1]` prompt boundary for one selected document.
- Separate document-source stream event and source card.
- Metadata-only citation persistence in migration 15.
- No-selection compatibility and stale-document rejection.

## Verification

- Backend lint and static typing pass.
- Full backend suite passes with at least 90% coverage.
- Frontend lint, static typing, tests, and production build pass.
- Focused tests prove document text is absent from metadata APIs.
- Focused tests prove a changed file is rejected before the user message is
  persisted.
- Focused tests prove the selected ID is sent, `[D1]` is displayed, and source
  metadata survives conversation reload.
- Repository whitespace validation passes.

## Release evidence

- Pull request 4 passed backend, frontend, Windows-control, and isolated
  production-runtime checks on exact head
  `10f64c8176c4ce159ea04cd67c028936a04fc67b`.
- Pull request 4 was merged with merge commit
  `618db48b8a655fdb054d9ff7bb34079814a1860a`.
- The same four checks passed again on protected `main`.
- A verified database backup and knowledge snapshot were created before
  installation.
- The Windows-host runtime reports release 0.63.0 and exposes only loopback
  ports.
- Live acceptance selected `ci-smoke-invoice.txt` for one turn, returned the
  exact invoice number and total, cited `[D1]`, and retained the verified source
  metadata after conversation reload.
- The browser interface displayed the Milestone 63 selector, the response, and
  the separate `[D1]` source card.

No release blocker remains. Semantic search, automatic retrieval, uploads,
tools, web access, autonomous actions, and external providers remain excluded.
