# Milestone 70 - Engineering Review

**Review date:** 31 July 2026

**Release candidate:** 0.70.0

**Decision:** Pass; protected repository integration remains

## Changed implementation

- Shared phone navigation is compact, sticky, and consistent.
- Intake no longer drifts horizontally at the measured phone width.
- Chat uses a labelled conversation picker on phone and retains its desktop
  conversation list.
- The previously accepted sticky composer behavior is preserved.
- Focus places Next actions before project and goal reference cards.
- Navigation and approved-record links meet a 44-pixel minimum touch height.
- Long safeguards remain available in closed-by-default detail sections.
- Backend and frontend versions are aligned at 0.70.0.

## Verification completed

### Frontend

- ESLint: passed.
- TypeScript production build: passed.
- Vitest: 47 passed.
- Added regression coverage for progressive disclosure, the phone conversation
  picker, and Focus information order.

### Backend and controls

- Ruff: passed.
- Mypy: 34 source files, no issues.
- Pytest: 144 passed.
- Coverage: 93.43%, above the required 90%.
- Windows controller and launchers: structurally valid.
- Compose configuration: valid.
- Production containers: rebuilt successfully.
- Direct API and frontend health: passed.

### Phone-sized installed runtime

- Measured content width: 375 CSS pixels.
- Intake, Chat, and Focus document width matched the viewport; no horizontal
  page overflow remained.
- Primary navigation remained at the top after 620 pixels of page scrolling.
- Phone conversation picker: visible, 48 pixels high, 14 local conversations,
  no sideways overflow.
- Sticky composer: remained inside the chat section and within the viewport.
- Focus Next actions appeared before project and goal reference cards.
- Approved-record review links measured 44 pixels high.
- Optional technical sections were closed by default and remained accessible.
- Browser error and warning log: empty.

### Installed candidate and owner acceptance

- Direct backend, same-origin frontend, and private Tailscale HTTPS health:
  `ok` at 0.70.0.
- Docker publications: Windows loopback only.
- Tailscale Serve: tailnet-only; public Funnel off.
- SQLite integrity: `ok` at schema 16.
- Operational warnings: none.
- Desktop regression at 1280 by 800: no horizontal page overflow on Intake,
  Chat, or Focus.
- Physical-phone owner acceptance: passed across navigation, conversation
  selection, normal chat, sticky composer, Focus ordering, and optional
  explanations.
- Verified post-acceptance backup:
  `nova-20260731T113439.231344Z.db`, SHA-256
  `60ae3bb0295d360573fa4055943828fb49cb55c74bbbafe046864a6646949ff3`.

## Known non-blocking maintenance diagnostics

1. Existing dashboard tests emit React `act(...)` advisory output even though
   all assertions pass.
2. The Codex fallback package launcher is newer than NOVA's pinned pnpm, so
   local release checks invoke pnpm 9.15.5 explicitly. Dependencies and cache
   stay on N:.

## Engineering judgement

The release candidate is technically sound, owner accepted, and preserves
NOVA's accepted safety boundaries. It is safe to enter protected repository
integration. Merge and release remain conditional on the changed-file audit
and required GitHub checks.
