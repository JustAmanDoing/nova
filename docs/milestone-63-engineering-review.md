# Milestone 63 Engineering Review

**Date:** 30 July 2026

**Release candidate:** 0.63.0

**Decision:** Pass pending protected-main CI and Windows owner acceptance

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

## Remaining release gate

Protected pull-request checks, production-container verification, installation
from the accepted merge, and owner confirmation on the Windows host remain
required before the release is tagged.
