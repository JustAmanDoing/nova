# NOVA Engineering Continuity

**Established:** 10 August 2026  
**Revised:** 14 August 2026

**Scope:** development governance and cross-device continuity procedure. This document is not a current-project-status authority; the live Google Drive **NOVA Handoff** is.

## Canonical current-status record

NOVA has one current project-status and cross-device continuity record:

**Google Drive document: `NOVA Handoff`**

Only that live document determines:

- the latest owner-accepted milestone;
- the active milestone and current work;
- current blockers and unresolved items;
- owner decisions affecting active work;
- the current completion estimate; and
- the exact next action or owner question.

The Handoff is not the authority for every fact in the project. Use the system that owns each fact:

- **Protected `main`, branches, pull requests, commits, Actions, tags, releases, and repository history:** code, proposed code, review state, technical checks, publication, and technical history.
- **Verified Windows runtime and physical PC/phone checks:** installation, health, local operation, private phone access, and owner acceptance.
- **Approved repository documents:** stable architecture, engineering policy, operations, specifications, milestone evidence, and historical technical records.
- **Chat discussion:** proposals, analysis, and owner decisions pending durable recording when they affect current project state.

Those sources support the Handoff within their own boundaries; they do not replace it as the answer to “Where are we up to with NOVA?”

Do not create or promote a second active status document, issue, branch, local file, database record, or summary.

## Start-of-session workflow

Every ChatGPT, Codex Remote, PC, or phone-controlled NOVA engineering session must complete this sequence before making a current-status claim or starting status-dependent engineering work:

1. Perform a fresh read of the canonical Google Drive `NOVA Handoff` through the connected Google Drive tool.
2. Establish the last owner-accepted milestone, active work, blockers, unresolved items, completion estimate, and exact next action from that read.
3. Inspect GitHub, approved repository documents, and relevant runtime or physical evidence only for facts needed by the requested work.
4. Reconcile discrepancies without creating another project-status authority.
5. Inspect the actual local checkout before local changes; a clean checkout may still be stale or on the wrong branch.

If `NOVA Handoff` cannot be located or read, stop before project-status claims or status-dependent engineering work and report exactly:

`CURRENT STATUS NOT VERIFIED`

Do not fall back to GitHub status text, chat memory, local archives, packaged project files, or old project mirrors.

A discrepancy does not transfer authority away from the Handoff. Investigate whether code, release, runtime, acceptance evidence, a stable project document, or the Handoff itself needs a verified correction. Record the resolved current project state in the Handoff and keep supporting technical evidence in the system that owns it.

## Handoff content discipline

The Handoff must stay useful as a live continuity record rather than becoming another historical archive.

Its active state should make these facts easy to identify:

1. latest owner-accepted milestone;
2. active milestone and workstream;
3. current blocker or unresolved evidence;
4. current completion estimate;
5. last completed step relevant to the active work; and
6. one exact next action or one exact owner question.

The **EXACT NEXT ACTION** section must contain one current actionable step or question. A roadmap, multi-stage process, historical date sequence, or complete milestone plan must not be stored there. Put durable process in its approved repository document and keep dated decisions clearly historical so they cannot compete with the live next action.

When project state changes, edit or replace the existing active-state wording instead of appending another contradictory “current” snapshot. Historical release hashes, old test runs, prior blockers, and superseded sequencing should remain in their authoritative history unless they are still necessary to interpret the present state.

The Handoff may retain concise supporting identifiers such as the current integrated commit, release, or installed version when they materially help continuity, but detailed historical evidence belongs in GitHub, runtime evidence, or approved historical documents.

## When the Handoff must change

Update the Handoff when authoritative project state changes, including when any of the following changes materially:

- active or accepted milestone state;
- an owner decision affecting current work;
- a blocker, unresolved item, or blocker resolution;
- review or verification evidence that changes confidence, acceptance, or the next work;
- branch, commit, pull-request, release, installation, or physical-acceptance state relevant to current work;
- completion estimate; or
- exact next action or owner question.

A pure read-only inspection, review, or verification that discovers no new decision, blocker, material evidence, status change, completion-estimate change, or next-action change must **not** create a no-op Handoff revision merely to prove the session occurred.

## Handoff write and verification workflow

When an update is required:

1. Reconcile the final repository, CI, release, runtime, acceptance, and owner-decision evidence relevant to the state change.
2. Update the existing active state in `NOVA Handoff`; do not create a new status document or append a competing current-state block.
3. Record only the current state needed for continuity, including the exact next action or question.
4. Perform a fresh Google Drive readback after the write.
5. Verify that the intended state is present and that no contradictory active status remains.
6. Only then report the state update as complete.

A write is not verified merely because the information exists in chat, model memory, cached content, another file, or an earlier connector response.

## Stale project-status artifact hygiene

The owner has issued a standing instruction to remove redundant project-status artifacts once they are verified stale or superseded rather than retaining parallel active copies.

For this rule, a **stale project-status artifact** means an artifact whose project-status function has been superseded and whose content is no longer uniquely required to preserve evidence, recovery, legal/security history, or another authoritative role.

Before removal, verify all of the following:

1. the target is not the canonical Google Drive `NOVA Handoff`;
2. no active process still treats it as authoritative;
3. its unique evidence, if any, is preserved in the system that owns that evidence;
4. removal will not damage recovery, auditability, legal/security history, or an approved historical record; and
5. the exact target is unambiguous.

Prefer reversible removal where the platform supports it. Permanent deletion is permitted under this standing instruction only for this verified redundant project-status class. A historical milestone document, Git commit, release record, audit event, backup, or unique engineering evidence is not stale merely because it is old.

## Retired continuity artifacts

The following names may remain in historical Git commits, superseded references, or compatibility history, but they are not active status sources and must not be recreated as project-status authorities:

- `project-status/STATUS.md`
- `scripts/Test-NovaContinuity.ps1`
- `NOVA - CURRENT_SPRINT`
- `NOVA - DAILY_SUMMARY`

Any compatibility reference that remains in active code or documentation must clearly identify these artifacts as retired and direct current-status questions to Google Drive `NOVA Handoff`.

## Approval and safety boundary

Reading or updating the Handoff does not authorize a merge, release, installation, product-scope expansion, data mutation, destructive action outside the verified stale-status class above, network change, dependency, provider, plugin, agent, or autonomous runtime action.

The engineering lead recommends technical direction. The owner retains approval authority for product scope, architecture acceptance, protected merge, release, live installation, material authority changes, destructive operations outside standing pre-approved classes, and physical acceptance.
