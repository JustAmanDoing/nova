# Milestone 69 - Secure Tailnet Phone Access Acceptance

**Date:** 31 July 2026

**Release candidate:** 0.69.0

**Branch:** `agent/milestone-69-secure-phone-access`

**Current decision:** Not release-ready; private phone use and controlled
disable are accepted, but re-enable recovery and protected release integration
are still required.

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
   validation pass; the corrected re-enable path still requires host evidence.

## Resolved external blocker

Tailscale certificate provisioning previously returned HTTP 500 while creating
the ACME DNS challenge record for this node. Provisioning later completed
without weakening NOVA's private-only boundary.

The installed certificate is valid for the exact private DNS name. Private
HTTPS health, Chat, Focus, and the same-origin API now pass. No router port,
public Funnel, or broader Docker listener was opened.

## Remaining acceptance

- Controlled re-enable recovery with the corrected Windows TLS health check
- Protected merge, installed-main rebuild, verified final backup, tag, and
  release

## Exact next action

Run the corrected `Phone Access On.cmd` as administrator and prove the same
private address recovers on the phone. Do not merge or release 0.69.0 until
that evidence and the protected integration sequence pass.
