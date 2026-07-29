# Milestone 63 Architecture Review

**Date:** 30 July 2026

**Release candidate:** 0.63.0

**Decision:** Pass

## Reviewed change

Milestone 63 adds an explicit selector for one currently indexed, ready intake
document per chat turn. The backend independently revalidates the intake
boundary, indexed fingerprint, current file fingerprint, extraction state, and
8,000-byte context limit before persisting the user's message.

## Architecture findings

- The existing modular monolith remains unchanged.
- Intake remains the authoritative source of document metadata and extracted
  text.
- Chat owns turn composition and citation persistence.
- No vector database, semantic-search service, RAG framework, plugin, agent,
  tool, external provider, or new process was added.
- The no-selection path retains the existing Milestone 59 behavior.
- Database migration 15 is ordered, transactional, and additive.

## Safety and privacy findings

- Selection is explicit and visible.
- Only one indexed intake record can be requested.
- Relative paths are resolved and rechecked beneath the configured intake root.
- SHA-256 is recalculated before the turn is stored.
- Oversized, stale, missing, duplicate, or unready sources are rejected.
- Document text is labelled as untrusted reference data.
- Selector and citation responses contain metadata only.
- Completed assistant replies retain exact fingerprint evidence.
- NOVA receives no additional file, network, tool, or action capability.

## Decision

The implementation preserves NOVA's local-first, privacy-first,
owner-controlled, guarded, reversible, and modular-monolith principles.
Architecture review passes with no release blocker.
