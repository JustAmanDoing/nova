# Milestone 74 - Accurate Capability Guidance Implementation

**Date:** 3 August 2026

**Target release:** 0.74.0

**Status:** Implemented, installed, and owner accepted; protected integration
remains

## Defect corrected

When the owner asked how to improve NOVA and use it to its fullest potential,
the local model replied with generic assistant boilerplate and incorrectly made
a blanket claim that it could not access documents or tools. That answer hid
verified NOVA capabilities and made the product less useful even though the
underlying local features were working.

## Implemented

- The Chat system guidance now gives the local model an exact, bounded account
  of NOVA's current capabilities:
  - private local Ollama chat;
  - owner-approved knowledge retrieval on each turn;
  - editable review cards for explicit remember requests;
  - one explicitly selected eligible local document for the current turn;
  - New chat, Rename, Archive, recoverable Trash, and Restore;
  - the wider Focus view and owner-entered next actions.
- Capability and configuration questions must lead with product-specific
  capabilities, then state exact limits and one action NOVA can really support.
- Guidance explicitly prevents blanket claims that local knowledge or selected
  documents are unavailable.
- Guidance prevents example requests that imply unavailable reminders,
  scheduling, sending, file actions, web lookup, or autonomous execution.
- Guidance prevents invented citation labels, document identifiers, text
  commands for interface controls, and session-wide document-selection claims.
- A provider-path regression test inspects the real system message delivered to
  the local model and locks these capability and boundary statements in place.
- Backend and frontend version records now identify candidate `0.74.0`.

## Architecture, safety, and privacy

- This is a prompt-and-test defect correction inside the existing Chat service.
- No endpoint, database schema, dependency, provider, listener, background job,
  permission, tool, plugin, agent, or autonomous action was added.
- Chat still cannot operate Focus or next-action controls; it may only explain
  that those guarded controls exist elsewhere in NOVA.
- Permanent knowledge still requires the owner's explicit **Approve & save**.
- A local document remains available only after explicit selection and only for
  that turn.
- Docker remains loopback-only and private phone access remains tailnet-only
  through Tailscale Serve with Funnel off.

## Recovery evidence

Before installation, NOVA created verified backup
`nova-20260803T073108.114632Z.db`. Its recorded SHA-256 was:

`76f7450fdf7a28054c068f627da601f562ae8dcabfea41ba5fdfedfcc10747ae`

After installed-runtime and real-model testing, NOVA created verified backup
`nova-20260803T074345.588089Z.db`. Its API-recorded and independently
recalculated SHA-256 both equal:

`477215292adaa60c2a00eb8cc57cf8fe5099180ed2f38da0dabde13bb327c65e`

## Exact next action

Integrate the owner-accepted candidate through the protected pull-request
workflow, rebuild the exact merged `main` runtime, and publish Release 0.74.0
only after the merged-runtime evidence passes.
