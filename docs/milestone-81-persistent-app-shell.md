# Milestone 81 - Persistent App Shell and Workspaces

**Status (11 August 2026): owner-approved implementation is complete on the
feature branch and locally verified. The candidate is not merged, released,
installed, or physically accepted.**

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
renders its unchanged feature content inside that shared boundary. Chat keeps
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

The existing Intake test suite still emits known React `act(...)` warnings in
two asynchronous state tests. All affected tests pass, and this candidate does
not change those state flows.

## Preserved boundaries and limitations

- Navigation uses the existing five HTML entry points; it does not introduce
  client-side routing or change workspace data ownership.
- The shell is visually persistent between workspaces, while switching an
  entry point still performs a normal page navigation.
- Local browser review used the built static frontend without the NOVA backend,
  so expected unavailable/404 states were visible while layout was assessed.
- Physical PC and private-phone acceptance remain required after reviewed
  merge and guarded installation.
- Release `v0.80.0` and authoritative `main` commit `c0bee2a` remain the latest
  released repository state until this candidate completes review and merge.

## Exact next action

Run a fresh independent diff review, then open a draft pull request and require
all protected CI checks before asking the owner to approve merge.
