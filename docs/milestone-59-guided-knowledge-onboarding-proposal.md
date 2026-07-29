# Milestone 59 Proposal — Guided Knowledge Onboarding

**Proposal date:** 29 July 2026

**Proposed base:** accepted Milestone 58 release 0.58.0

**Status:** Approved, implemented, and owner accepted on 29 July 2026

## Purpose

Milestone 58 can identify useful knowledge gaps. Milestone 59 should make each
gap easy to act on through natural conversation without requiring the owner to
create files, understand the filing structure, or approve information in
advance.

The workflow remains:

1. NOVA identifies a published missing or review-due area.
2. The owner chooses one suggestion.
3. NOVA prepares one focused, editable prompt.
4. The owner completes and sends it.
5. Existing deterministic capture prepares a review card.
6. The owner edits, approves, or rejects the proposed record.
7. Knowledge health refreshes only after the existing approved lifecycle
   action succeeds.

## Bounded runtime scope

### Missing knowledge

- Add an **Add through chat** control to missing suggestions.
- Insert a category-specific starter into the chat composer.
- Place keyboard focus in the composer.
- Do not send the message automatically.
- Do not create a candidate until the owner sends the completed message.
- Reuse the existing proposal and **Approve & save** controls.

Examples:

- Preferred name: `Remember that my preferred name is …`
- Response style: `Remember that I prefer responses that …`
- Current goals: `Remember that my current goal is …`
- Active projects: `Remember that my active project is …`

### Review-due knowledge

- Show the matching approved record title.
- Provide a **Review record** control that opens the existing lifecycle editor.
- Reuse immutable revision and typed retirement controls.
- Do not silently mark information current.
- A future explicit “confirmed unchanged” event is outside this proposal unless
  separately reviewed and approved.

### Quality refresh

- Refresh the read-only quality report after successful approval, update, or
  retirement.
- Keep a failed refresh isolated from chat and record lifecycle actions.
- Make the resulting score change explainable through the matched record list.

## Explicit exclusions

- No automatic interviews or repeated questioning.
- No automatic sending.
- No automatic approval or permanent memory.
- No bulk profile generation.
- No inference from ordinary chat history.
- No file upload requirement.
- No embeddings or semantic classification.
- No web, cloud, email, calendar, tools, plugins, or agents.
- No redesign of the knowledge catalog.

## Architecture assessment

The proposal should reuse the existing quality response, chat composer,
deterministic candidate service, approval endpoint, and immutable lifecycle
controls. It should not introduce a second knowledge-writing path or another
source of truth.

The preferred implementation is frontend orchestration with a small published
prompt-template map. Backend work is limited to any schema detail required to
make a matched review-due record unambiguous. A database migration is not
expected.

## Safety requirements

- A suggestion click only prepares local UI state.
- The owner must send the completed prompt.
- The owner must separately approve the resulting proposal.
- Optional areas remain explicitly optional.
- Existing mutation-intent headers remain mandatory.
- Every approved record remains path- and checksum-verified.
- No overwrite, deletion, upload, or external transmission is added.

## Acceptance criteria

1. Selecting a missing core area prepares the correct editable prompt.
2. Nothing is sent or saved until the owner performs the existing actions.
3. Rejecting the prepared proposal leaves coverage unchanged.
4. Approving it adds one verified record and refreshes the matching area.
5. Selecting an optional area preserves its Optional label and wording.
6. A review-due area identifies the exact matched active record.
7. Keyboard and 390 px layouts remain usable.
8. A quality refresh failure does not break chat or approval.
9. The complete automated and production verification matrix passes.
10. Live Windows and owner acceptance pass before release completion.

## Decision

The owner explicitly approved the bounded runtime work on 29 July 2026.
Implementation remains subject to architecture, engineering, live Windows, and
owner acceptance before the milestone is complete.
