# Milestone 74 Proposal - Accurate Capability Guidance

**Date:** 3 August 2026

**Proposed base:** accepted release 0.72.0

**Status:** Owner-requested corrective scope

## Goal

Make NOVA accurately explain how the owner can get more value from the current
system. Lead with verified local capabilities, state exact boundaries without
overgeneralising them, and offer one practical next step instead of generic
assistant boilerplate.

## Approved behavior

The Chat system guidance will identify these currently verified capabilities:

1. private conversation through the local Ollama model;
2. relevant owner-approved knowledge checked for each turn;
3. explicit remember requests producing editable approval cards;
4. one explicitly selected eligible local document per turn;
5. local conversation organisation and recovery; and
6. Focus and owner-entered next actions in the wider NOVA interface.

When asked how to improve, configure, or get more value from NOVA, the model
should explain relevant current capabilities, state honest limitations, and
suggest one high-value next step based on supplied context.

## Boundaries

- Do not claim web browsing, automatic document retrieval, unselected file
  access, sending, scheduling, file actions, or autonomous execution.
- Do not imply that Chat directly operates Focus or next-action controls.
- Do not change memory approval, retrieval, document selection, action
  authority, networking, storage, or conversation behavior.
- Add no dependency, database migration, API endpoint, provider, listener,
  plugin, agent, or telemetry.
- Do not hard-code private owner data into the prompt.

## Acceptance

- Prompt-level regression tests prove the verified capability and boundary
  guidance reaches the model.
- The exact owner question receives product-specific guidance from the real
  installed local model without the false blanket claim that documents or all
  tools are unavailable.
- Existing memory, document, chat, safety, and release tests remain green.
- The owner confirms the result is materially more useful.
