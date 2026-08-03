# Milestone 76 Proposal - Local NOVA Project Record

**Date:** 3 August 2026

**Proposed base:** accepted Release 0.74.0

**Status:** Explicitly requested and approved by the owner; architecture and
engineering reviews passed with conditions

## Goal

Make NOVA's approved project history and current state locally durable and
inspectable without depending on ChatGPT chat history.

## Approved first slice

1. Create a canonical current project-status record from exact repository,
   release, runtime, knowledge, archive, and milestone evidence.
2. Create a local catalogue of existing authoritative and supporting sources.
3. Expose the catalogue and bounded plain-text source review through NOVA on PC
   and private phone access.
4. Add a guarded host-side control to import one explicitly selected NOVA-only
   chat or project source with a checksum and no overwrite.
5. Keep raw imported sources separate from approved knowledge.
6. Show measured migration coverage and clearly identify what remains only in
   ChatGPT or has not been supplied.
7. Add verified archive evidence and recovery instructions.

## Explicit exclusions

- automatic access to the ChatGPT account or browser session;
- automatic export or deletion of ChatGPT chats;
- import of unrelated personal conversations;
- semantic search, embeddings, vector storage, or background indexing;
- automatic summarisation or promotion into permanent knowledge;
- model-decided source authority or trust;
- external upload, sharing, Git tracking of raw sources, or cloud sync;
- secret extraction, credential storage, or clipboard monitoring;
- editing or deleting source archives through the web interface.

## Source priority shown in NOVA

1. current Git repository and release documentation;
2. verified installed runtime and acceptance evidence;
3. approved checksum-bound knowledge;
4. dated local project/session records;
5. raw imported chat sources, labelled unapproved evidence.

## Acceptance

Release requires automated, Windows runtime, archive-integrity, desktop,
phone-size, and physical-owner checks. The owner must confirm that the Project
record is understandable and that it does not imply every ChatGPT chat has
already been imported.
