# Milestone 79 - Librarian Plain-Language Correction

**Decision date:** 9 August 2026

**Base release:** 0.78.2

**Status:** Owner-requested correction in review; not released or installed

## Owner feedback

The owner reported that Home responsibilities is useful, but the Librarian's
technical wording makes some suggestions hard to understand. The owner also
confirmed that Emergency plan is not needed.

## Bounded decision

Use everyday wording throughout the Librarian and its suggestion list, including
the four suggestions currently shown by the live store. This prevents technical
phrases from returning when another suggestion appears later. Keep every
identifier, matching phrase, score, priority, issue order, API field, safety
boundary, and review link unchanged.

This is a copy correction, not a new capability. No external library or service
solves repository-specific wording, so the reuse-first result is to keep the
existing service and interface and change only their displayed text.

## Safety boundary

- The Librarian remains read-only.
- No suggestion is dismissed automatically.
- No knowledge is added merely to clear the queue.
- No database, schema, dependency, deployment, network, model, or permission
  changes are authorised.
- Any future Ignore action or detection-rule change remains a separate product,
  architecture, and engineering decision.

## Acceptance target

The owner should be able to understand each suggestion without engineering
terms. In particular, Home responsibilities becomes Home jobs and projects,
and the interface explains that suggestions can be ignored and nothing changes
unless the owner chooses.

Physical owner acceptance is still required after a protected merge and
installation. Until then, Release 0.78.2 remains authoritative.

## Remaining limitation

The Emergency contacts or plan suggestion still appears because this correction
does not add an Ignore action or change detection rules. That remains a separate
owner decision.

## Exact next action

The owner reviews the wording in draft PR #34 and explicitly approves or rejects
it. No merge or installation happens before that decision.
