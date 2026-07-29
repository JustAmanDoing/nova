# Milestone 58 — Architecture Review

**Review date:** 29 July 2026

**Prototype release:** 0.58.0

**Decision:** Accepted

## Assessment

Knowledge Quality and Gap Analysis fits the existing modular monolith as a
read-only view over the established knowledge service. It introduces no second
source of truth, no schema migration, no background worker, and no new
deployment component.

The authoritative inputs remain owner-approved SQLite records and their
immutable Markdown files. The report verifies the active files before
measuring them and fails closed on an integrity error. It cannot promote,
change, retire, delete, upload, or share knowledge.

## Boundary review

- Local-first and privacy-first: preserved.
- Owner approval before permanent knowledge: unchanged.
- Explicit mutation guard: unchanged; the report is GET-only.
- Authoritative originals and immutable revisions: preserved.
- Local deterministic retrieval: reused behind its existing service boundary.
- Modular-monolith architecture: preserved.
- AI optional for core operation: preserved; scoring uses no model.
- No silent assumptions: preserved through published matching criteria.
- Failure isolation: accepted; report failure does not disable chat.

## Trade-offs

The catalog is intentionally small and deterministic. This lowers apparent
coverage compared with semantic inference, but keeps every result explainable
and prevents NOVA from treating guesses as approved personal facts.

The report recalculates on request rather than introducing cached state. This
is appropriate for the current record volume and avoids cache invalidation or
another mutable store. The retrieval check is bounded at 100 active records so
the request remains predictable as the library grows.

## Conditions

- Keep catalog changes code-reviewed and documented.
- Do not add an owner “completion” score; measure NOVA capability only.
- Do not make optional information part of core coverage.
- Do not use this report to trigger automatic memory creation.
- Measure endpoint latency before adding caching or background processing.

No architectural blocker remains for Milestone 58 owner acceptance.
