# Milestone 59 — Architecture Review

**Review date:** 29 July 2026

**Prototype release:** 0.59.0

**Decision:** Accepted

## Assessment

Guided Knowledge Onboarding is a frontend orchestration layer over existing
Milestone 55–58 contracts. It adds no API endpoint, database migration,
background worker, deployment component, mutable cache, or second knowledge
source.

Missing-area controls prepare only local component state. Permanent knowledge
continues through the established chat, deterministic candidate, and explicit
approval path. Review-due controls navigate to the existing immutable
lifecycle editor using the matched record identifier already published by the
read-only quality response.

## Boundary review

- Local-first and privacy-first: preserved.
- Owner approval before permanent knowledge: preserved.
- Existing mutation guard: unchanged.
- Immutable revisions and typed retirement: reused.
- Approved records and Markdown files remain authoritative.
- Modular-monolith architecture: preserved.
- AI remains optional for core quality and navigation behavior.
- Failure isolation: preserved.
- No silent assumptions or freshness changes: preserved.

## Trade-offs

The published prompt map is deliberately deterministic. It cannot improvise a
personalised interview, but its behavior is inspectable and prevents an
untrusted model response from becoming a second onboarding path.

The interface shows the five highest-value gaps rather than every catalog item.
This keeps the page focused while leaving the complete report available through
the same read-only service.

## Conditions

- Keep preparation separate from sending.
- Keep sending separate from permanent approval.
- Do not infer new prompt content from chat history.
- Do not treat opening a stale record as a review event.
- Any future confirmed-unchanged lifecycle action requires a separate review.

No architectural blocker remains within the approved Milestone 59 scope.
