# Milestone 81 - Persistent App Shell and Workspaces

**Status (12 August 2026): owner-approved implementation is complete on the
feature branch and has been reconciled with protected `main` at
`aff23ba19d3cb5b9c32839e2a84d9ae62b15c7a2` through merge commit
`9f3a575d10c5537d37b9e95f2e1aefcbb4373fda`. Local verification and the
initial independent diff review are complete. The final review corrected the
closed mobile drawer so its hidden links cannot receive pointer or keyboard
focus, and made the privacy wording accurately describe NOVA's local/private
boundary. Exact-head protected CI and final verification are still required on
the corrected candidate. The candidate is not merged, released, installed, or
physically accepted.**

## Approved decision

The owner approved a bounded user-interface change: give NOVA one persistent
application shell, feature-specific workspaces, responsive side navigation,
and a ChatGPT-style Chat layout. No unrelated feature changes are approved.

This implementation preserves the existing five workspace boundaries:

- **Chat** - conversation history, model selection, transcript, and composer;
- **Focus** - approved projects, goals, and owner-entered next actions;
- **Record** - the local NOVA project record;
- **Librarian** - read-only knowledge-health guidance; and
- **Intake** - incoming-file review and guarded execution.

## Reuse and implementation

The candidate reuses the existing React multi-page application, workspace
entry points, design tokens, Chat conversation panel, and responsive controls.
It adds no dependency, router, backend endpoint, data migration, network
surface, AI authority, storage layer, or second source of truth.

`frontend/src/AppShell.tsx` owns the common shell and navigation semantics.
`frontend/src/app-shell.css` owns its desktop rail, phone header, drawer,
backdrop, focus states, and reduced-motion behavior. Each existing workspace
renders its existing feature content inside that shared boundary. Chat keeps
conversation history as a distinct secondary panel and uses dedicated phone
controls for history and new-chat actions.

## Verification evidence

Local verification on 11 August 2026:

- TypeScript project type check - passed.
- ESLint - passed.
- Complete Vitest frontend suite - 60 tests passed across 6 files.
- Production Vite build - passed; 46 modules transformed and all five HTML
  entry points emitted.
- Browser review at 1440 x 900 - passed: 236 px persistent navigation,
  300 px Chat history, no horizontal overflow.
- Browser review at 1024 x 768 - passed: persistent navigation and Focus
  workspace align without horizontal overflow.
- Browser review at 390 x 844 - passed: 294 px workspace drawer, separate Chat
  history overlay, usable model/composer controls, and no horizontal overflow.
- Initial independent `main...HEAD` diff and whitespace review - passed with no
  blocking defect or scope expansion found.

Reconciliation and final review on 12 August 2026:

- Current `main` was four commits ahead because PR #44 replaced the former
  GitHub-first continuity workflow with Google Drive `NOVA Handoff` as the sole
  current project-status authority.
- PR #44 changed `AGENTS.md`, `docs/engineering-continuity.md`, and the retired
  compatibility checker only; none overlaps the Milestone 81 product files.
- Current `main` was merged into the feature branch without changing the
  Milestone 81 product diff.
- The mobile drawer previously remained focusable while translated off-screen.
  The final review corrected this with delayed `visibility` and pointer-event
  handling, while preserving the opening and closing animation.
- The shell privacy note now says data stays local and private rather than
  inaccurately saying it never leaves the PC; private phone use remains valid.
- Protected CI must pass on the final corrected head. The pull-request checks,
  not this historical document, are authoritative for that exact-head result.

The existing Intake test suite still emits known React `act(...)` warnings in
two asynchronous state tests. All affected tests pass, and this candidate does
not change those state flows.

## Preserved boundaries and limitations

- Navigation uses the existing five HTML entry points; it does not introduce
  client-side routing or change workspace data ownership.
- The shell is visually persistent between workspaces, while switching an
  entry point still performs a normal page navigation.
- This milestone exposes only the five workspaces NOVA already implements. The
  approved dedicated owner file **Library** workspace is not implemented by
  this PR; **Librarian** is knowledge-health guidance, not the file Library.
  Library remains a separate implementation step under the approved product
  direction.
- Local browser review used the built static frontend without the NOVA backend,
  so expected unavailable/404 states were visible while layout was assessed.
- Physical PC and private-phone acceptance remain required after reviewed
  merge and guarded installation.
- Release `v0.80.0` and protected `main` commit
  `aff23ba19d3cb5b9c32839e2a84d9ae62b15c7a2` remain the latest integrated
  repository state until this candidate completes review and merge.
- Google Drive `NOVA Handoff` remains the sole current project-status authority;
  this document is implementation evidence only.

## Exact next action

Run protected CI on the final corrected PR head and complete the final evidence
check. If it passes, request the owner's explicit approval to mark PR #43 ready
and merge it. Release, installation, physical acceptance, and the dedicated
Library workspace remain separate later gates.
