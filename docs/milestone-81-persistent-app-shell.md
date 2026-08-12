# Milestone 81 - Persistent App Shell and Workspaces

**Status (12 August 2026): the reviewed implementation was owner-approved and
merged through PR #43 into protected `main` at
`d88fd00c950291ff79b5b9922e6dc2d4249ecca6`. Exact-candidate protected CI run
`31549576713` and post-merge protected-`main` run `31550946912` both passed
Backend quality, Frontend quality, Windows controls, and Production runtime.
Release preparation proposes NOVA `0.81.0` on a separate branch. The milestone
is integrated but is not yet released, installed, or physically accepted.**

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

The implementation reuses the existing React multi-page application, workspace
entry points, design tokens, Chat conversation panel, and responsive controls.
It adds no dependency, router, backend endpoint, data migration, network
surface, AI authority, storage layer, or second source of truth.

`frontend/src/AppShell.tsx` owns the common shell and navigation semantics.
`frontend/src/app-shell.css` owns its desktop rail, phone header, drawer,
backdrop, focus states, scrolling behavior, and reduced-motion behavior. Each
existing workspace renders its existing feature content inside that shared
boundary. Chat keeps conversation history as a distinct secondary panel and
uses dedicated phone controls for history and new-chat actions.

## Verification evidence

Local verification on 11 August 2026:

- TypeScript project type check - passed.
- ESLint - passed.
- Complete Vitest frontend suite - 60 tests passed across 6 files.
- Production Vite build - passed; 46 modules transformed and all five HTML
  entry points emitted.
- Browser review at 1440 x 900 - passed: persistent navigation, Chat history,
  and no horizontal overflow.
- Browser review at 1024 x 768 - passed: persistent navigation and Focus
  workspace align without horizontal overflow.
- Browser review at 390 x 844 - passed: responsive workspace drawer, separate
  Chat history overlay, usable model/composer controls, and no horizontal
  overflow.
- Initial independent `main...HEAD` diff and whitespace review - passed with no
  blocking scope expansion.

Reconciliation and final review on 12 August 2026:

- PR #44 replaced the former GitHub-first continuity workflow with Google Drive
  `NOVA Handoff` as the sole current project-status authority.
- Current `main` was reconciled into the feature branch without changing the
  Milestone 81 product scope.
- The final review corrected the closed mobile drawer so hidden links cannot
  receive pointer or keyboard focus.
- The navigation rail was made scrollable on short displays.
- The shell privacy note was corrected to describe NOVA's local/private
  boundary accurately, including private phone use.
- Exact-candidate protected CI run `31549576713` passed Backend quality,
  Frontend quality, Windows controls, and Production runtime.
- PR #43 was marked ready and merged only after explicit owner approval.
- Post-merge protected-`main` run `31550946912` passed Backend quality,
  Frontend quality, Windows controls, and Production runtime against exact
  merge commit `d88fd00c950291ff79b5b9922e6dc2d4249ecca6`.

The existing Intake test suite still emits known React `act(...)` warnings in
two asynchronous state tests. All affected tests pass, and this milestone does
not change those state flows.

## Preserved boundaries and limitations

- Navigation uses the existing five HTML entry points; it does not introduce
  client-side routing or change workspace data ownership.
- The shell is visually persistent between workspaces, while switching an
  entry point still performs a normal page navigation.
- This milestone exposes only the five workspaces NOVA already implements. The
  approved dedicated owner file **Library** workspace is not implemented by
  Milestone 81; **Librarian** is knowledge-health guidance, not the file
  Library. Library remains a separate implementation step under the approved
  product direction.
- Physical PC and private-phone acceptance remain required after release and
  guarded installation.
- The latest published release and installed runtime remain NOVA `0.80.0` until
  the separately approved release and installation process succeeds.
- Google Drive `NOVA Handoff` remains the sole current project-status authority;
  this document is implementation and release evidence only.

## Release preparation

The proposed release is NOVA `0.81.0`. The release-preparation branch aligns the
backend package, API-reported version, and frontend package version, and adds a
bounded release and guarded-installation plan. It does not authorize a merge,
tag, GitHub release, Windows update, or owner acceptance.

Release and installation plan:

- `docs/milestone-81-release-installation-plan.md`

## Exact next action

Complete exact-head protected CI and independent review of the Milestone 81
release-preparation pull request. If both pass, request one explicit owner
approval covering the preparation merge, `v0.81.0` publication, guarded Windows
installation, and physical PC/private-phone acceptance. Do not execute those
actions before approval.
