# Milestone 79 - Librarian Plain-Language Correction

**Decision date:** 9 August 2026

**Base release:** 0.78.2

**Status:** Merged through PR #34 and installed; its current wording was later
extended by PR #35 and owner-accepted on PC and phone

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

PR #35 later made the separately approved name **Home jobs and routines** and
added optional static examples. That current installed wording preserves this
plain-language decision.

PR #34 merged at `d60799dc56ebc10174076e9b98fb3659b7075fd6` after all
protected checks passed. That commit was installed and validated on the Windows
NOVA runtime. PR #35 then merged at
`93daa9806590c950c94044e637a44125f5739ec0`, was installed through the guarded
updater, preserved owner data, and was accepted on the physical PC and phone.
Release 0.78.2 remains the authoritative version. The complete current evidence
is recorded in `docs/milestone-79-knowledge-examples-acceptance.md`.

## Remaining limitation

The Emergency contacts or plan suggestion still appears because this correction
does not add an Ignore action or change detection rules. That remains a separate
owner decision.

## Exact next action

Begin a separate evidence-led capability discussion. No Milestone 80 runtime
scope is approved before architecture review, engineering review, and explicit
owner approval.
