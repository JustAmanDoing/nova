# Milestone 75 - Architecture Review

**Review date:** 3 August 2026

**Reviewed proposal:** Milestone 76 Local NOVA Project Record

**Decision:** Passed with conditions

## Architectural fit

The proposal fits the modular monolith as a read-only project-record module.
It does not create a second project-management system or replace Git, release
evidence, approved knowledge, the local database, or raw source archives.

Authoritative sources retain their existing ownership:

1. Git and repository documentation remain authoritative for code and release
   decisions.
2. Verified runtime results remain authoritative for installed state.
3. Approved knowledge remains authoritative for owner-approved facts, goals,
   preferences, projects, lessons, rules, and references.
4. Raw imported chat sources remain immutable evidence, not approved facts.
5. The project record is a derived catalogue with explicit source labels and
   freshness information.

## Required boundaries

1. Store the host archive under `N:\Nova\Archive`, outside Git and C:.
2. Mount the archive read-only inside the backend container.
3. Resolve every catalogue path beneath one configured archive root and reject
   traversal, links escaping the root, and unsupported file types.
4. Enforce bounded file counts, preview lengths, and source sizes.
5. Keep raw imports no-overwrite and checksum-bound.
6. Require explicit host invocation and typed confirmation before importing a
   supplied source.
7. Never scan the ChatGPT account, browser profile, clipboard, or unrelated
   filesystem paths automatically.
8. Never promote imported content into approved knowledge automatically.
9. Never put raw chat exports, personal content, secrets, or runtime manifests
   into Git or release evidence.
10. Keep the catalogue useful without Ollama.
11. Keep PC and phone access inside the accepted loopback plus private
    Tailscale same-origin boundary.
12. Preserve original sources and append-only manifests; correction creates a
    new manifest entry rather than rewriting source evidence.

## Privacy and safety review

Pass with conditions.

- The owner selects each source explicitly.
- No external API, connector, provider, telemetry, or upload is introduced.
- Raw source text is never sent to the model merely by opening the catalogue.
- The UI distinguishes raw evidence, approved knowledge, repository evidence,
  and current verified status.
- A full-account ChatGPT export must be rejected by default because it may
  contain unrelated personal conversations.
- The import control records metadata and checksum but never claims content is
  accurate, approved, current, or safe to retrieve.
- Existing backups must be extended or accompanied by a verified archive
  manifest so the new local dependency is recoverable.

## Modular-monolith decision

No new service, database, vector store, worker, plugin, or agent is justified.
One backend service, versioned API route, frontend view, and guarded Windows
control are sufficient for a single-owner local archive.

## Architecture acceptance conditions

- The current status points to exact release, tag, branch, commit, and source
  evidence.
- The catalogue remains readable if Ollama is stopped.
- An absent or empty archive returns a valid empty report.
- A malformed manifest or inaccessible source is isolated and reported rather
  than suppressing the remaining catalogue.
- Path traversal, oversized source, duplicate source, unsupported extension,
  and missing local-intent/import confirmation tests pass.
- Docker remains loopback-only and Tailscale Funnel remains off.
- Existing knowledge, chat, Focus, Intake, backup, restore, and guarded-action
  tests remain green.

## Conclusion

Milestone 76 is architecture-conformant if it remains a local, read-only-first,
source-aware catalogue with a separate guarded host import boundary.
