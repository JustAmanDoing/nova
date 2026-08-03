# Milestone 76 - Acceptance Record

**Date:** 3 August 2026

**Release candidate:** 0.76.0

**Status:** Passed; implementation merged and exact merged-main runtime
verified; evidence-only integration, tag, and publication remain

## Automated checks passed

- Backend Ruff passed.
- Backend strict mypy passed for all 37 source files.
- Backend pytest passed 158 of 158 tests.
- Backend coverage passed at 93.11 percent against the 90 percent requirement.
- Frontend ESLint passed.
- Frontend TypeScript passed.
- Frontend Vitest passed 51 of 51 tests.
- Frontend production build passed and includes `archive.html`.
- Windows launcher/control structural validation passed.
- Docker Compose configuration validation passed.
- Changed-file whitespace validation passed.

The existing non-failing React `act(...)` warnings remain in older dashboard
tests. They predate this feature and do not affect the 51 passing assertions.

## Guarded import checks passed

- One synthetic NOVA-only text source imported into an isolated acceptance
  archive after the exact typed confirmation.
- The imported copy matched its source SHA-256:
  `bb1ca6667b19c93659754c9f9b3b5b3b1a3affd8df6f9f988dc22c90a7fdbec3`.
- Its authority remained `raw_unapproved`.
- A duplicate import was rejected without overwrite.
- A full ChatGPT `conversations.json` account export was rejected.
- Production `N:\Nova\Archive` was not altered by the synthetic import test.

## Installed-runtime checks passed

- Backend and frontend containers are running; backend is healthy.
- Local health reports candidate version `0.76.0`.
- The active database passed NOVA's read-only SQLite integrity check.
- The Project Record API reports 142 sources, 142 verified, zero changed, zero
  missing, zero invalid, and zero raw chat sources supplied.
- The archive bind mount is read-only inside the backend container.
- Local `/archive.html` returned HTTP 200 with the expected page title.
- Security headers remain active, including the same-origin content security
  policy, frame denial, no-referrer policy, and disabled camera, microphone,
  and geolocation permissions.
- Recent container logs contain no matching error, exception, traceback, fatal,
  or panic event.
- Docker ports remain bound to Windows loopback.

## Desktop and phone-sized browser checks passed

- The Record view exposes the current release, verification counts, migration
  boundary, grouped source catalogue, and bounded source preview.
- A verified current-status record opened and displayed its checksum-bound local
  content.
- The first physical-phone attempt exposed that the preview was placed below all
  142 records. Release acceptance paused, the preview was changed to an immediate
  phone panel, and the exact private-route tap was reproduced after rebuilding.
- The corrected phone preview occupies the visible viewport, scrolls internally,
  focuses its 44-pixel **Close** control, supports Escape dismissal, and does not
  cause horizontal overflow.
- At 390 by 844 phone size, the page has no horizontal overflow.
- Summary cards, source cards, and 44-pixel controls remain readable and usable.
- The small-screen navigation deliberately hides only the already-open page;
  **Record** remains available from Chat and successfully navigates back to the
  archive.
- The page explicitly states that unsupplied ChatGPT conversations have not
  been migrated.
- Browser console inspection found no warning or error entries.

## Private phone-route checks passed

- `https://nova.tail1d0293.ts.net/archive.html` returned HTTP 200.
- The private Project Record API returned the same 142/142 verified state.
- The private route passed at phone size without horizontal overflow.
- Tailscale Serve remains tailnet-only and Funnel remains off.

## Recovery checks passed

- Pre-install database backup:
  `nova-20260803T090345.816532Z.db`.
- Recorded SHA-256:
  `200faef35f783653cb368205c3a3c475597b5f0d5a251f326c64b9640323d850`.
- Pre-install archive index and current status were preserved under
  `N:\Nova\Backups\Pre-Milestone-76`.

## Physical-owner acceptance

The owner opened the private **Record** page on the phone. The first attempt
found the buried-preview defect. After the correction was installed, the owner
opened `NOVA-Current-Status` again and confirmed that the immediate on-screen
preview passed.

## Current release-readiness decision

All automated, installed-runtime, recovery, privacy, architecture, desktop,
phone-sized browser, private-route, and physical-owner checks passed. Protected
implementation integration and exact merged-main verification also passed.

## Exact merged-main verification

- Protected implementation PR #22 passed all four required GitHub checks and
  merged with merge commit
  `6bd2c654027b0c56462d05582a873face109069b`.
- The merge tree exactly matched accepted feature head
  `466914969a5c4e357d59c1f039ae7264fa064ced`, and the feature branch remains
  available.
- Rebuilding from exact merged `main` produced healthy NOVA `0.76.0` services.
- SQLite integrity, local/private Record HTTP responses, archive read-only
  mounting, loopback port binding, tailnet-only Tailscale Serve, and runtime
  log checks all passed again.

Milestone 76 is approved for evidence-only protected integration, tag, and
publication. No runtime defect remains open.
