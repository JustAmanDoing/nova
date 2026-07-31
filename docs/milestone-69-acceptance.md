# Milestone 69 - Secure Tailnet Phone Access Acceptance

**Date:** 31 July 2026

**Release candidate:** 0.69.0

**Branch:** `agent/milestone-69-secure-phone-access`

**Implementation PR:** #13

**Implementation merge commit:**
`cfa2cbd881a1520b0d05bba1ae30003077b7885f`

**Current decision:** Release approved. Runtime, recovery, protected merge,
merged-main checks, installed-main rebuild, private phone health, and final
backup verification all pass.

## Checks passed

- The authenticated Tailscale node is online with the exact private DNS name
  `nova.tail1d0293.ts.net`.
- Tailnet HTTPS consent is enabled and the node advertises the expected
  certificate domain.
- Tailscale Serve has one HTTPS reverse proxy from the private DNS name to
  `http://127.0.0.1:5173`.
- The live Serve configuration exactly matches NOVA's ignored local ownership
  record.
- No `AllowFunnel` flag is true; the route is not public.
- Frontend and backend Docker publications remain bound only to `127.0.0.1`.
- Local same-origin health returns `ok` for NOVA `0.69.0`.
- The complete GitHub matrix passes on draft PR #13: backend quality, frontend
  quality, production runtime, and Windows controls.
- Private Serve/Funnel classification tests cover empty, private false-flag,
  public true-flag, and foreground public configurations.
- The private HTTPS certificate is valid for `nova.tail1d0293.ts.net` and the
  HTTPS Chat, Focus, and same-origin API routes return successfully.
- The owner verified Chat, Focus, approved knowledge, and a genuine reversible
  next-action workflow from the phone.
- The owner verified that the mobile chat composer stays within reach while
  the conversation scrolls, then stops at the end of the chat section instead
  of covering the Knowledge panels.
- The mobile-composer correction passes frontend lint, type checking, all 46
  frontend tests, and the production build.
- `Phone Access Off.cmd` removed the exact NOVA-owned Serve configuration and
  ownership record. The private HTTPS address stopped accepting connections,
  while desktop NOVA remained healthy at `0.69.0`, both containers remained
  healthy, and the database read-only integrity check passed.
- The corrected `Phone Access On.cmd` restored the exact NOVA-owned private
  Serve configuration. The owner confirmed phone recovery, and an independent
  health request returned `ok` for `0.69.0` through the private HTTPS address.
- After recovery, Funnel remains off, the live Serve configuration matches the
  ignored ownership record, both Docker publications remain loopback-only, and
  desktop health and database integrity still pass.
- Verified pre-merge backup
  `nova-20260731T110735.375682Z.db` was created with SHA-256
  `955d583ff0239c52cf5fcc97b626fe958fe40ced9c019dd766fe9a64a395c3a0`.
- PR #13 was marked ready only after all four required checks passed, then
  merged with merge commit `cfa2cbd881a1520b0d05bba1ae30003077b7885f`.
  The implementation branch remains on GitHub for traceability.
- Protected `main` repeated backend quality, frontend quality, production
  runtime, and Windows-control checks successfully.
- The authoritative Windows checkout and `origin/main` both resolve to
  `cfa2cbd881a1520b0d05bba1ae30003077b7885f`.
- The installed Windows release was rebuilt from that exact `main`. Local and
  private HTTPS health report `0.69.0`, Funnel remains off, Docker remains
  loopback-only, and database integrity passes.
- Verified final backup `nova-20260731T111156.769809Z.db` was created after the
  installed-main rebuild with SHA-256
  `955d583ff0239c52cf5fcc97b626fe958fe40ced9c019dd766fe9a64a395c3a0`.

## Acceptance defects corrected

1. Missing HTTPS consent previously allowed the launcher to rebuild before the
   Tailscale command waited. The controller now stops before changing runtime,
   reports the exact approval URL, and explains the Windows administrator
   requirement.
2. Tailscale 1.98 returns the shared Serve configuration from both `serve
   status --json` and `funnel status --json`. NOVA now detects public exposure
   from true `AllowFunnel` flags rather than from a non-empty document.
3. Long knowledge panels initially separated phone conversations from the
   message composer. The composer now follows the transcript in document order
   and remains anchored within reach while the chat section scrolls. A
   regression test preserves that ordering.
4. The first recovery re-enable attempt reached the private HTTPS health check
   but Windows PowerShell reported that it could not create a secure TLS
   channel. The controller now explicitly enables TLS 1.2 for that bounded
   check, restores the prior process setting afterward, and allows 120 seconds
   for private Serve readiness instead of 45. Parser and Windows structural
   validation pass. The corrected re-enable path then passed on the Windows
   host and the owner confirmed phone recovery.

## Resolved external blocker

Tailscale certificate provisioning previously returned HTTP 500 while creating
the ACME DNS challenge record for this node. Provisioning later completed
without weakening NOVA's private-only boundary.

The installed certificate is valid for the exact private DNS name. Private
HTTPS health, Chat, Focus, and the same-origin API now pass. No router port,
public Funnel, or broader Docker listener was opened.

## Remaining publication

- Merge this final evidence through the protected release-evidence pull
  request, then tag that evidence merge as `v0.69.0` and publish GitHub release
  **Release 0.69.0**.

## Exact next action

Publish the accepted release, then begin **Milestone 70 - Phone Daily-Use
Validation** without adding runtime authority.
