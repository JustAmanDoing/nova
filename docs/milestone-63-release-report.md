# Milestone 63 Release Report

**Date:** 30 July 2026

**Release:** 0.63.0

**Decision:** Pass

## Outcome

NOVA can use one explicitly selected, ready local intake document for one chat
turn. It verifies the current path and SHA-256 before storing the user message,
adds bounded text as untrusted `[D1]` context, and persists citation metadata
only. The owner can see the selected source separately from approved personal
knowledge.

## Source integration

- Feature branch:
  `agent/milestone-63-explicit-document-context`
- Accepted feature head:
  `10f64c8176c4ce159ea04cd67c028936a04fc67b`
- Pull request: 4
- Merge method: merge commit
- Merge commit:
  `618db48b8a655fdb054d9ff7bb34079814a1860a`
- Feature branch preserved

## Completed checks

- Backend lint and static typing passed.
- Full backend suite passed: 130 tests and 92.92% total coverage.
- Frontend lint, static typing, 34 tests, and production build passed.
- Windows launcher and controller validation passed.
- Isolated production-container acceptance passed.
- The complete protected check set passed on the pull-request head.
- The same check set passed again on protected `main`.
- Repository whitespace, hygiene, secret-pattern, and documentation-link checks
  passed.
- No generated output, local data, credentials, secrets, or temporary files
  entered the merge.

## Recovery evidence

Before installation, NOVA created and independently hashed:

- database backup `nova-20260729T210544.669080Z.db`
  - SHA-256:
    `025dca5a2c02a66b566c9cd3b61f219bd5fda78afb03d29ba2d33c8b9221b9ec`
- knowledge snapshot `nova-knowledge-20260729T210544.907905Z.zip`
  - SHA-256:
    `e66f220562fa45c10fa0f7a98eba16f6bad5b0fd637a08a0a4127ec6a94e658c`

Both recovery artifacts remain on the N drive.

## Windows-host acceptance

- The API health endpoint reported version 0.63.0.
- Backend and frontend containers were healthy and bound only to
  `127.0.0.1`.
- Migration 15's `chat_message_document_sources` table was present.
- Seven currently eligible documents appeared in the metadata-only selector.
- A live turn explicitly selected `ci-smoke-invoice.txt`.
- NOVA returned invoice `TXT-ACCEPT-001`, total `$35.15 AUD`, and citation
  `[D1]`.
- Reloaded history retained the exact filename, SHA-256, type, and citation
  label without duplicating the document text.
- The browser UI showed the selected-document control and separate `[D1]`
  source card.

## Architecture and safety findings

- Local-first operation is preserved.
- API and UI remain loopback-only.
- Original files remain authoritative and unchanged.
- Selection is explicit and limited to one document for one turn.
- Validation occurs before the user message is stored.
- Document content is treated as untrusted reference data.
- No file action, network tool, or autonomous capability is granted to the
  model.
- Existing approved-knowledge retrieval remains separate.
- The modular monolith remains intact.

## Risks and limitations

- Context is intentionally limited to one ready document and 8,000 UTF-8 bytes.
- The feature does not search or select documents automatically.
- A local model can still answer imperfectly; the source card and fingerprint
  remain the evidence boundary.
- Semantic search, uploads, broad library browsing, tools, voice, remote access,
  plugins, agents, automation, and external AI remain out of scope.

## Release recommendation

Release 0.63.0 is safe to tag after this evidence-only documentation change
passes the protected pull-request and post-merge checks.

## Exact next milestone

Milestone 64 — Evidence-Led Next Capability Selection. It may prepare and
review a proposal, but no new runtime capability is authorized until the owner
explicitly approves the selected scope.
