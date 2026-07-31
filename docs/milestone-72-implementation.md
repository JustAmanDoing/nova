# Milestone 72 - Conversation Organisation Implementation

**Date:** 1 August 2026

**Target release:** 0.72.0

**Status:** Implemented; automated, installed-runtime, and simulated-phone
acceptance passed; physical-phone owner acceptance remains

## Implemented

- Chat opens the most recently active conversation and positions its bounded
  transcript at the latest exchange.
- Messages remain in chronological order and **Jump to latest** appears when
  the owner reviews earlier messages.
- **New chat** is directly reachable on phone and desktop.
- A phone **Chats** drawer exposes conversation selection and all lifecycle
  controls without moving the composer away from the current exchange.
- Active conversations may be renamed, archived, or moved to recoverable
  Trash after explicit confirmation.
- Archived and trashed conversations remain locally reviewable and restorable
  with their complete message history.
- Permanent purge is not implemented.
- Schema migration 17 adds conversation archive and Trash state plus an
  append-only lifecycle-event table.
- Created, renamed, archived, restored, trashed, and restored-from-Trash events
  are written atomically with their state changes.
- Lifecycle mutation and message submission are rejected while that
  conversation is generating a reply.

## Safety and privacy

- Every lifecycle mutation uses the existing local owner-intent guard.
- Archive and Trash never delete or rewrite a message.
- Existing conversation identifiers, timestamps, sources, citations, and
  model metadata remain authoritative in the current SQLite database.
- The existing verified backup, restore, integrity, and migration controls are
  reused unchanged.
- No external service, dependency, listener, provider, sync, telemetry,
  semantic search, plugin, or agent was added.
- Docker remains published only to Windows loopback and private phone access
  remains Tailscale Serve with Funnel off.

## Source changes

- `backend/app/api/routes/chat.py`
- `backend/app/schemas/chat.py`
- `backend/app/services/chat.py`
- `backend/app/services/database.py`
- `backend/tests/test_chat.py`
- `backend/tests/test_database.py`
- `frontend/src/ChatApp.tsx`
- `frontend/src/ChatApp.test.tsx`
- `frontend/src/chat.css`
- `frontend/src/lib/api.ts`
- version, proposal, review, roadmap, README, acceptance, and release records

## Recovery evidence

Before migration, NOVA created verified backup
`nova-20260731T221224.862373Z.db`. Its recorded and independently recalculated
SHA-256 both equal:

`bd110ae8efc7590571810ae75b98a2af159c6b2f9ff8da7b09fef5e3743966dd`

## Exact next action

Complete the physical-phone owner check, then integrate the protected release
candidate using a merge commit and verify the exact merged `main` runtime.
