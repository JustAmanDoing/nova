# Milestone 74 - Architecture Review

**Review date:** 3 August 2026

**Decision:** Pass

The correction changes only the existing Chat system guidance and tests. It
does not add a component, interface, database state, network path, provider,
tool, or action authority. The modular monolith, local Ollama adapter, SQLite
source of truth, explicit document-selection boundary, approved-knowledge
retrieval boundary, and owner approval model remain unchanged.

The prompt must distinguish three layers clearly:

- what the local language model can discuss;
- what verified context NOVA supplies for a turn; and
- what guarded controls the owner can operate elsewhere in NOVA.

This prevents capability understatement without encouraging the model to
claim actions it cannot perform. Local-first, privacy-first, AI-optional core
operation, auditability, and reversibility are preserved.
