# Milestone 59 — Guided Knowledge Onboarding

**Date:** 29 July 2026

**Base commit:** `49095772ada1c933a44b0a77c313a547777fe3b7`

**Working branch:** `agent/milestone-59-guided-knowledge-onboarding`

**Prototype release:** 0.59.0

**Decision:** Accepted

## Scope delivered

- Every displayed missing knowledge area provides an **Add through chat**
  control.
- Selecting the control inserts one category-specific, editable
  `Remember that...` starter and moves keyboard focus to the chat composer.
- The prepared prompt remains unsent and creates no candidate or permanent
  record until the owner completes and sends it.
- Every displayed review-due area shows the exact matched approved record title
  and provides a **Review record** control.
- Review opens the existing immutable lifecycle editor for that exact record.
- Optional areas remain clearly labelled Optional.
- Existing proposal review, explicit **Approve & save**, immutable revision,
  typed retirement, quality refresh, and local mutation guards are reused.

## Safety behavior

A suggestion click changes local browser state only. It does not call a
mutation endpoint, send a chat message, create a candidate, approve knowledge,
change freshness, or write a file.

Missing knowledge still requires two deliberate owner actions:

1. complete and send the prepared chat message; and
2. review and select **Approve & save** on the resulting proposal.

Review-due knowledge still requires the owner to make an actual change before
**Save new revision** becomes available. NOVA does not silently mark a record
current merely because it was opened.

## Automated verification

- Ruff passed.
- Strict mypy passed for 31 application source files.
- 128 backend tests passed at 92.80% coverage.
- ESLint passed.
- TypeScript passed.
- 34 frontend tests passed.
- The production frontend build passed.
- Backend and frontend production image builds passed.
- Docker Compose validation passed.
- Windows controller structural validation passed.
- Git whitespace validation passed.

Focused regressions prove:

- a missing core prompt is prepared and focused;
- the suggestion click makes no network request;
- the safety notice states that nothing was sent or saved;
- optional status and wording remain visible;
- review due identifies and opens the exact matched record; and
- the existing quality-failure isolation remains intact.

## Live Windows evidence

- Production health reports version 0.59.0.
- Backend and frontend containers run locally; the backend is healthy.
- Both published ports remain bound only to `127.0.0.1`.
- The live quality report verifies 3 active records and a 3-of-3 retrieval
  self-check.
- Selecting **Add through chat** for Current goals prepared
  `Remember that my current goal is ` and focused the composer.
- The live status notice stated: `Nothing has been sent or saved.`
- Pending candidate count remained zero.
- The newest conversation retained its existing two-message count.
- The temporary test prompt was cleared without sending it.
- The phone-width browser override showed no horizontal overflow and retained
  a usable composer and action control.
- The browser console contained no warnings or errors.

## Preserved boundaries

- No automatic send, approval, save, update, retirement, or deletion.
- No automatic interview or repeated questioning.
- No inference from ordinary chat history.
- No second knowledge-writing path or source of truth.
- No database migration, background worker, or deployment component.
- No file upload requirement, embeddings, semantic classification, web,
  cloud, email, calendar, tools, plugins, or agents.
- `main` and `origin/main` remain unchanged.

## Current limitations

- Prompt starters are intentionally short and deterministic.
- Only the five highest-ranked missing or review-due items are displayed.
- Review-due live behavior is regression-tested but the current synthetic
  production records are not old enough to create a live stale item.
- The existing non-failing React `act(...)` warnings in intake dashboard tests
  remain and predate this milestone.

## Recovery

Pre-Milestone-59 checkpoints are stored under:

`N:\Nova\Backups\Pre-Milestone-59`

Database:

`nova-20260729T091232.969776Z.db`

SHA-256:

`dab9874386ef89223c41a7dfc8ee9d26ccb2f616ca1ac7e1025c57dd859ec4f1`

Knowledge snapshot:

`nova-knowledge-20260729T091233.164600Z.zip`

SHA-256:

`97577eb2ddd642760bcfe62110372af97b49939b8022f02d0212cda14821416c`

Post-Milestone-59 checkpoints are stored under:

`N:\Nova\Backups\Post-Milestone-59`

Database:

`nova-20260729T092520.171366Z.db`

SHA-256:

`dab9874386ef89223c41a7dfc8ee9d26ccb2f616ca1ac7e1025c57dd859ec4f1`

Knowledge snapshot:

`nova-knowledge-20260729T092520.369143Z.zip`

SHA-256:

`76bba79d2442ea207ca6d41870a402767a5abb57565bf591fbc531edbe857d6b`

## Exact next action

Select and explicitly approve the bounded product scope of Milestone 60 before
beginning more runtime work.

## Owner acceptance

The owner exercised the installed end-to-end workflow on 29 July 2026:

1. selected a missing Preferred name area;
2. completed and sent the prepared prompt;
3. reviewed the generated candidate;
4. selected **Approve & save**; and
5. supplied visual evidence of the refreshed quality report.

The approved `Name is Lyle` record is active, path- and checksum-tracked, and
matched deterministically to Preferred name. Live core coverage rose from 0%
to 16.7%, freshness is 100%, and retrieval self-checking passes for all 4
active records.

Final accepted-state checkpoints are stored under:

`N:\Nova\Backups\Post-Milestone-59-Accepted`

Database:

`nova-20260729T094338.115509Z.db`

SHA-256:

`025dca5a2c02a66b566c9cd3b61f219bd5fda78afb03d29ba2d33c8b9221b9ec`

Knowledge snapshot:

`nova-knowledge-20260729T094338.326237Z.zip`

SHA-256:

`c3bfc4e4dab9a981068caba7f93f0d76f80a25f1242640b912eadd39194a9942`

## GitHub publication

The verified cumulative branch was pushed to GitHub on 29 July 2026:

`agent/milestone-59-guided-knowledge-onboarding`

Draft pull request:

`https://github.com/JustAmanDoing/nova/pull/1`

Remote `main` remains unchanged at
`210a39f88dc0acadb9ec2e12d0c4d4e8053cf687`. Review and merge remain separate
from the accepted local installation.
