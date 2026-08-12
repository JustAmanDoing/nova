# NOVA Engineering Continuity

**Established:** 10 August 2026  
**Revised:** 12 August 2026

**Scope:** development governance and cross-device continuity; no NOVA runtime
or product behavior change

## Single authoritative project-status record

NOVA has one current project-status and cross-device continuity record:

**Google Drive document: `NOVA Handoff`**

Only that document determines:

- the latest completed milestone;
- current work;
- blockers and unresolved issues;
- approved decisions affecting current work; and
- the exact next action.

GitHub remains authoritative for code, pull requests, commits, Actions results,
tags, releases, and technical history. The verified Windows runtime and physical
checks remain authoritative for installation, health, local operation, private
phone access, and owner acceptance. Those sources support and verify the
Handoff; they do not replace it as the answer to “Where are we up to with
NOVA?”

The former GitHub-first status path is retired. Do not use the `project-status`
branch, `STATUS.md`, or `scripts/Test-NovaContinuity.ps1` to determine current
project status. `CURRENT_SPRINT` and `DAILY_SUMMARY` are also retired and must
not be recreated as active project-status documents.

Historical milestone, release, architecture, and engineering documents remain
valid evidence for the work they record. Chat memory, ChatGPT project mirrors,
exports, archives, packaged project files, and stale local checkouts are never
current-status authorities.

## Start-of-session workflow

Every ChatGPT, Codex Remote, PC, or phone-controlled NOVA engineering session
must complete this sequence before making a current-status claim or starting
work:

1. Locate and read the exact Google Drive document named `NOVA Handoff`.
2. Use its completed milestone, current work, blockers, approved decisions, and
   exact next action as the project-status baseline.
3. Inspect GitHub and the relevant runtime only for the supporting facts needed
   by the requested work.
4. Reconcile supporting evidence without creating or promoting another status
   record.
5. Inspect the actual local checkout before local changes; a clean checkout may
   still be stale or on the wrong branch.

If `NOVA Handoff` cannot be located or read, stop before project-status claims
or engineering work and report exactly:

`CURRENT STATUS NOT VERIFIED`

Do not fall back to GitHub status text, chat memory, local archives, or old
project files.

A discrepancy does not transfer authority away from the Handoff. Investigate
whether code, release, runtime, acceptance, or the Handoff itself needs a
verified correction. Record the resolved current state in the Handoff and keep
supporting technical evidence in the system that owns it.

## End-of-session workflow

Every engineering session that materially changes, verifies, reviews, merges,
releases, installs, accepts, or blocks NOVA work must update `NOVA Handoff`
before reporting completion:

1. Reconcile the final repository, CI, release, runtime, acceptance, and owner-
   decision evidence relevant to the session.
2. Update the Handoff’s active state rather than creating a new status document.
3. Record the resulting milestone state, completed work, checks, branch, exact
   commit, pull-request and release/install state, blockers or risks, current
   completion estimate, and one exact next action.
4. Read the Google Doc back after the write.
5. Verify that the returned text contains the intended current state and does
   not retain a contradictory active status.
6. Only then report the work session complete.

This update is mandatory and must not depend on an owner reminder.

## Authority boundaries

- **Google Drive `NOVA Handoff`:** current project status and cross-device
  continuity.
- **Protected `main`:** integrated source code.
- **Feature branches and pull requests:** proposed code and review state.
- **GitHub Actions:** checks run against an exact commit; passing CI proves only
  those checks.
- **GitHub tags and releases:** publication evidence, not installation.
- **Verified Windows runtime and physical PC/phone checks:** installation,
  health, and owner acceptance.
- **Approved repository documents:** architecture, engineering decisions,
  operations, milestone evidence, and historical technical records.
- **Chat discussion:** proposals and owner decisions pending durable recording.

No source may silently claim authority outside its boundary. Do not create a
second active status issue, branch, file, document, database record, or summary.

## Retired continuity artifacts

The following names may remain in historical commits, superseded documents, or
compatibility checks, but they are not active status sources:

- `project-status/STATUS.md`
- `scripts/Test-NovaContinuity.ps1`
- `NOVA - CURRENT_SPRINT`
- `NOVA - DAILY_SUMMARY`

Any retained compatibility artifact must clearly state that it is retired and
must direct users to Google Drive `NOVA Handoff`. It must not calculate, publish,
or validate the current milestone or next action.

## Approval and safety boundary

Reading or updating the Handoff does not authorize a merge, release,
installation, scope expansion, data mutation, destructive action, network
change, dependency, provider, plugin, agent, or autonomous runtime action.
Existing owner approvals and NOVA’s development playbook continue to govern
those actions.
