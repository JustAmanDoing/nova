# Milestone 78 - The Librarian Architecture Review

**Decision date:** 5 August 2026

**Status:** Approved by the owner before implementation

## Decision

The Librarian is a first-class core service in NOVA's existing modular
monolith. It consumes the current approved knowledge store, immutable revision
history, checksums, deterministic duplicate logic, quality report, and review
workflow. It is not a second database, memory store, model, plugin, or agent.

## Responsibility

The service may identify and explain:

- deterministic duplicate candidates;
- potential conflicts supported by explicit structural evidence;
- review-due knowledge;
- missing checklist coverage;
- missing files, broken local references, and checksum failures; and
- recorded sources and candidate confidence.

Every result includes its rule, evidence, affected records, evidence strength,
and a suggested owner action. The result may link to the existing knowledge
review workflow.

## Authority boundary

The Librarian has no write endpoint and creates no persistent review table. It
must never edit, merge, retire, delete, rewrite, upload, or infer knowledge. It
does not invent a truth resolution for conflicting statements. Material change
continues to require the existing owner-controlled knowledge workflow.

## Data flow

`Approved knowledge -> Librarian analysis -> Read-only health and review views`

SQLite and immutable Markdown records remain authoritative. Computed review
items use deterministic identifiers and disappear when their evidence no longer
exists. This preserves one knowledge source of truth and avoids stale parallel
state.

## Conflict boundary

The MVP flags a potential conflict only when two or more verified active records
have the same normalized title and different normalized content. This proves a
structural disagreement without claiming which content is correct. Broader
semantic or model-based conflict inference remains out of scope.

## Architecture conclusion

The approved design preserves local-first, privacy-first, AI-optional operation
and the modular monolith. No schema migration, external service, background
worker, autonomous action, or new authority boundary is required.
