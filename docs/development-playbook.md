# NOVA Development Playbook

**Recorded:** 9 August 2026

**Status:** Development System Foundation; documentation and governance only

## Purpose

This playbook defines how NOVA moves from an idea to an owner-accepted Windows
installation. It is inserted before further runtime work so phone-controlled
development remains consistent, reviewable, and safe.

It does not change the NOVA runtime, authorize a product agent, or begin
Milestone 79. A future product-facing Conductor remains a separate product
architecture decision; development agents and Remote controls are engineering
tools, not NOVA runtime authority.

## Required flow

```text
Discuss
  -> Research and reuse check
  -> Architecture Review
  -> Engineering Review
  -> Owner approval
  -> Codex implementation
  -> Verification
  -> Review
  -> Pull request and protected CI
  -> Owner-approved merge
  -> Install
  -> Owner acceptance
  -> Project-state update
```

No arrow is implied by the previous step. Each gate must produce its own
evidence, and the owner may stop, defer, or redirect the work.

## Gates and outputs

### 1. Discuss

Owner and ChatGPT define the problem, desired outcome, user experience,
non-goals, privacy expectations, and whether the need is measured or only
speculative. Discussion produces a candidate direction, not implementation
authority.

### 2. Research and reuse check

The engineering lead inspects the live repository, installed environment, and
current official platform capabilities before proposing custom code.

For each likely component:

1. Verify what NOVA already implements.
2. Verify what the current development and runtime platforms already provide.
3. Search for proven free and open-source solutions.
4. Evaluate license, security, privacy, local operation, recovery, maintenance,
   integration cost, and authority boundaries.
5. Record whether NOVA should reuse, integrate, extend, or build a small local
   component, and why.

Current-capability research is mandatory when ChatGPT, Codex, Remote, GitHub,
Docker, Tailscale, Ollama, Windows, or NOVA may already solve the problem. Use
official current documentation plus installed or repository evidence. Do not
build a replacement from model memory or an old feature assumption.

### 3. Architecture Review

The engineering lead defines ownership, sources of truth, data flow, trust and
network boundaries, approval points, failure behavior, recovery, and explicit
non-goals. The review must preserve the modular monolith unless measurements
justify a change.

### 4. Engineering Review

The engineering lead specifies the bounded modules, schemas, APIs, migrations,
dependencies, UI, tests, operational checks, rollout, rollback, and acceptance
criteria. It records the reuse decision and remaining custom code.

### 5. Owner approval

The owner and ChatGPT approve the product outcome and reviewed scope. Approval
must be explicit. Approval of a discussion, architecture direction, or nearby
milestone does not silently authorize a broader implementation.

### 6. Codex implementation

Codex on the Windows PC implements only the approved scope on the approved
branch or worktree. It preserves unrelated work, keeps commits focused, and
stops for any material product, authority, credential, destructive, external,
or network decision not already approved.

### 7. Verification

Codex runs the smallest checks that prove the changed boundary, plus required
regression and operational checks. Results are evidence, not approval. Failed
or skipped checks are reported truthfully.

### 8. Review

Review the complete diff for scope, safety, privacy, architecture, dependency,
recovery, documentation, and repository hygiene. Correct defects before
publication; do not use CI as the first intentional review.

### 9. Pull request and protected CI

Push the focused branch and open or update a draft pull request. GitHub records
the authoritative proposed diff, commits, review, and CI history. All required
checks must pass against the current candidate. Passing CI does not authorize a
merge.

### 10. Merge

Merge only after explicit owner approval and repository protections permit it.
Never push around protected `main`, force-push shared history, or merge a stale
or failing candidate.

### 11. Install

Install only the reviewed merged release through NOVA's guarded Windows update
process. Verify the exact commit or tag, create required backups, keep rollback
available, and do not treat an isolated container test as physical installation.

### 12. Owner acceptance

The owner validates the real Windows installation and any required physical
phone workflow. Synthetic tests support acceptance but do not replace it.

### 13. Project-state update

Record the accepted release and commit, verification, owner decision, remaining
limitations, unresolved issues, current completion estimate, exact next action,
and exact next milestone. Preserve history; do not rewrite a proposal as an
accepted release.

## Responsibilities

| Participant | Primary responsibility | Authority boundary |
| --- | --- | --- |
| Owner + ChatGPT | Product discussion, priorities, user experience, and explicit product approval | May approve, stop, defer, or redirect product work; discussion alone does not change code or runtime |
| Engineering lead | Architecture, current-capability research, reuse analysis, technical choices, engineering review, risk review, and acceptance design | Recommends technical direction but does not grant owner approval or merge authority |
| Codex on Windows PC | Bounded implementation, tests, builds, repository verification, draft PR publication, and evidence collection | Acts only inside approved scope and host permissions; stops at approval gates |
| ChatGPT/Codex Remote on phone | Primary remote control surface for starting, steering, approving, and reviewing PC chats | Inherits the connected PC chat's tools, credentials, sandbox, and approvals; it is not a second execution authority |
| GitHub | Authoritative code, branch, commit, pull-request review, and CI history | A passing check proves its check only; GitHub does not represent the installed runtime or owner acceptance |
| Windows NOVA installation | Authoritative physical runtime, local data, Windows controls, and final PC/phone acceptance environment | Changes require guarded install and owner approval; local runtime evidence does not rewrite repository history |

## Development capability matrix

| System | Capabilities to reuse first | Authoritative for | Boundary and verification before replacement |
| --- | --- | --- | --- |
| ChatGPT | Product discussion, projects and shared context, research, planning, long-running goals, and review | Owner conversation and explicit product decisions when recorded | Not authoritative for current code or runtime; verify current product features and connected sources before building NOVA equivalents |
| Codex | Repository inspection, durable `AGENTS.md` guidance, scoped editing, testing, terminal work, review, worktrees, and draft PR workflows | Evidence produced in the checked-out repository and host session | Must obey repository, sandbox, and approval boundaries; verify the current Codex surface before adding custom developer orchestration |
| Remote | Start or continue host chats, steer work, answer questions, approve actions, and review outputs, diffs, tests, terminal output, screenshots, and completion notifications | The owner's remote instructions and approvals in the connected chat | Requires an awake, online, paired host; inherits host permissions and does not replace GitHub or runtime evidence |
| GitHub | Protected branches, pull requests, reviews, Actions checks, commit and release history | Canonical source code and reviewed integration history | Required checks must pass on the current candidate; no merge without owner approval and no claim that CI equals installation |
| Docker | Compose service definition, reproducible builds, isolated runtime, health checks, and container boundaries | Container build and isolated runtime evidence | Does not own Windows host state or physical acceptance; inspect current Compose capabilities before adding another orchestrator |
| Tailscale | Authenticated tailnet connectivity and private HTTPS Serve for NOVA phone access | Current private network route and access-policy state | Keep Serve private and Funnel off; inspect live configuration before changes and never expose the app server or NOVA publicly by convenience |
| Ollama | Local model discovery, generation, and the local HTTP API | Available local models and local inference responses | Remains optional and non-authoritative; verify installed models/API and do not substitute cloud models or external endpoints without approval |
| Windows | Host filesystem, PowerShell controls, Docker Desktop, local credentials, physical devices, backups, and installed NOVA | Installed runtime and physical PC acceptance | Host mutations, elevation, credentials, services, storage, and installation require bounded controls and owner approval where material |
| NOVA | Existing Chat, Focus, Knowledge, Librarian, Intake, Project Record, review, audit, backup, and recovery workflows | NOVA domain data and guarded product actions | Extend the owning service instead of duplicating it; preserve local-first, approval, audit, and recovery boundaries |

## Agent permission boundaries

Development agents may perform read-only inspection, official research, scoped
edits, proportionate verification, focused commits, and explicitly requested
draft-PR updates without repeatedly asking for approval. These are safe only
inside the owner's stated task and repository scope.

Owner approval remains mandatory for product scope, architecture acceptance,
merge, release, live installation, material dependency or provider adoption,
credential and account changes, network exposure, destructive or irreversible
operations, owner-data transfer, and any expansion beyond the approved task.

No development-agent permission grants a NOVA runtime agent, plugin, model, or
service additional product authority.

## Phone-sized task design

Remote work should be easy to start and supervise from a phone. Each task should
fit this structure:

- **Outcome:** one observable result.
- **Scope:** the repository, branch, files, runtime, and people included.
- **Constraints:** safety, privacy, compatibility, non-goals, and actions to
  avoid.
- **Verification:** exact evidence that proves completion.
- **Approval points:** decisions that must return to the owner.
- **Handoff:** concise changed-files, checks, risks, commit, PR state,
  completion estimate, and exact next action.

Prefer one task per outcome. Split independent work into separate chats and
worktrees. Do not split a tightly coupled implementation merely to make more
agents busy.

## Verified Remote baseline

On 9 August 2026, the owner recorded that ChatGPT/Codex Remote had been
physically verified from the phone against chats running on the Windows PC.
This proves the phone can act as the primary remote development control surface
for the current setup. It does not prove every future tool, approval, browser,
or Computer Use path; verify the specific path when a task depends on it.

## Current capability references

- [Codex custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [ChatGPT/Codex Remote connections](https://learn.chatgpt.com/docs/remote-connections)
- [GitHub protected branches](https://docs.github.com/en/pull-requests/reference/branches)
- [GitHub status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [Docker Compose application model](https://docs.docker.com/compose/intro/compose-application-model/)
- [Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve)
- [Ollama local API](https://docs.ollama.com/api/introduction)
- [Windows developer environment](https://learn.microsoft.com/en-us/windows/dev-environment/)
