# Milestone 79 - Knowledge Examples Phase 1 Candidate

**Decision date:** 9 August 2026

**Implementation base:** `d60799dc56ebc10174076e9b98fb3659b7075fd6`

**Status:** Owner-approved bounded candidate; not merged, released, installed,
or owner-accepted

## Product decision

Give each of NOVA's 13 existing knowledge checks two short examples of useful
information the owner could add. Examples are optional blank-page guidance,
not facts about the owner. NOVA never saves or sends an example automatically.

The candidate also renames **Home jobs and projects** to **Home jobs and
routines**. Examples appear only for a missing check in Chat or after the owner
opens a missing Librarian check. Covered and review-due checks stay uncluttered.

Each example can prepare an editable Chat draft. The existing generic **Open**
handoff remains available. Preparing either draft performs no write, approval,
message send, or knowledge creation.

## Architecture review

- The existing backend knowledge-requirement catalogue remains the single
  source for names, explanations, generic prompt starters, example labels,
  example drafts, matching phrases, priorities, and review periods.
- The existing knowledge-quality response carries the catalogue guidance to
  Chat. The existing Librarian missing-coverage issue carries the same examples
  into its read-only detail response.
- The frontend renders returned guidance and owns only transient composer state.
  It has no requirement-specific example or prompt map.
- A linked example is untrusted URL text. Chat bounds it to the existing
  4,000-character composer limit and places it only in the editable composer.
  The normal explicit send and knowledge-approval workflows remain unchanged.
- There is no new store, migration, service, endpoint, dependency, model,
  permission, network path, or authority boundary.

This preserves the modular monolith, local-first and privacy-first operation,
read-only Librarian analysis, immutable knowledge revisions, and explicit owner
approval before permanent knowledge.

## Engineering review and reuse result

The current requirement catalogue, knowledge-quality API, Librarian issue
detail, Chat composer, and guarded knowledge proposal workflow already own the
needed path. No free or open-source library is appropriate for NOVA-specific
example copy; adding one would increase supply-chain and maintenance cost
without providing reusable behavior. The smallest solution is a backwards-
compatible schema extension and local rendering of static curated content.

The catalogue supplies two examples for every requirement. Relevant guidance
discourages secrets, passwords, account numbers, exact addresses, and
unnecessary medical detail. Time-based home and vehicle guidance says that NOVA
can remember the information but cannot send reminders yet.

## Explicit non-goals

- no personalised, generated, ranked, or learned suggestions;
- no reminders, notifications, recurring tasks, Planner, or calendar work;
- no Ignore or dismiss behavior;
- no detection, scoring, priority, issue-order, matching, or authority change;
- no automatic send, approval, save, or knowledge modification; and
- no database, dependency, provider, service, deployment, release, installation,
  or live-runtime change.

## Verification target

The candidate must pass the repository's backend, frontend, Windows, Compose,
isolated-runtime, responsive-browser, diff, link, whitespace, and protected-CI
checks. Tests must prove all 13 example sets, missing-only display, editable
draft handoff without a write, and byte-for-byte knowledge/database preservation.

## Current estimate

- Accepted practical local NOVA prototype: 100 percent.
- Broader long-term NOVA vision: approximately 86 percent.
- Milestone 79: approximately 85 percent when this candidate is verified in a
  draft PR; merge, guarded installation, and physical owner acceptance remain.

PR #33 remains the separate validation and installed-state evidence candidate.
This implementation does not modify that branch or its draft PR.

## Exact next action

After protected CI passes on the exact draft-PR head, the owner reviews the
examples and explicitly approves or rejects merging the candidate. Do not merge,
release, or install it before that decision.
