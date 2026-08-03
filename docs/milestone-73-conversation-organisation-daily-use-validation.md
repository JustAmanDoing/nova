# Milestone 73 - Conversation Organisation Daily-Use Validation

**Date:** 3 August 2026

**Base release:** 0.72.0

**Status:** Complete; one high-impact chat-guidance defect selected for
correction

## Evidence

The owner used NOVA Chat and asked how to improve NOVA so it could assist to
its fullest potential. NOVA replied with generic advice and said it could not
access external tools, documents, or real-time data.

The response was misleading in the current product context. NOVA already:

- checks relevant owner-approved local knowledge for every chat turn;
- prepares editable review cards from explicit remember requests;
- accepts one explicitly selected, eligible local document for a turn;
- provides local conversation history and reversible organisation; and
- provides Focus and owner-entered next actions elsewhere in the same local
  interface.

The response did not explain those capabilities, distinguish Chat authority
from the wider NOVA interface, or give the owner a useful next step.

## Verified root cause

The accepted Chat system prompt correctly restricts web access, automatic
document retrieval, and tool authority, but it describes restrictions without
describing NOVA's verified local capabilities. A local model can therefore
generalise the restriction into the false impression that NOVA cannot use
documents or local knowledge at all.

## Impact and urgency

This is a high-impact adoption defect. It makes NOVA understate its own value,
gives generic instructions where product-specific guidance is expected, and
can prevent the owner from discovering already accepted features. It does not
indicate data loss, privacy exposure, or unsafe action authority.

## Decision

Select **Milestone 74 - Accurate Capability Guidance** as a bounded corrective
release. Do not add a tool, web provider, autonomous action, external service,
new permission, or automatic data access.

## Completion estimate

- Accepted practical local NOVA prototype: 100 percent.
- Broader long-term NOVA vision: approximately 86 percent.
- Milestone 73 validation: 100 percent.

The broader estimate is unchanged because validation records evidence rather
than adding capability.
