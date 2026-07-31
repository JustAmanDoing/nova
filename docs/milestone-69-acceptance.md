# Milestone 69 - Secure Tailnet Phone Access Acceptance

**Date:** 31 July 2026

**Release candidate:** 0.69.0

**Branch:** `agent/milestone-69-secure-phone-access`

**Current decision:** Not release-ready; external certificate provisioning is
blocking phone-browser acceptance.

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

## Acceptance defects corrected

1. Missing HTTPS consent previously allowed the launcher to rebuild before the
   Tailscale command waited. The controller now stops before changing runtime,
   reports the exact approval URL, and explains the Windows administrator
   requirement.
2. Tailscale 1.98 returns the shared Serve configuration from both `serve
   status --json` and `funnel status --json`. NOVA now detects public exposure
   from true `AllowFunnel` flags rather than from a non-empty document.

## External blocker

TLS handshakes currently fail because the Tailscale control plane returns HTTP
500 while creating the ACME DNS challenge record for this node. A single
bounded retry produced the same result. Tailscale's public status page reported
the certificate service operational at the time, so no further automated
certificate retries were made.

The private Serve configuration is preserved so Tailscale can finish
certificate issuance later. Local desktop NOVA remains healthy and unchanged.

## Remaining acceptance

- Successful HTTPS health through the private Tailscale address
- Controlled disable and re-enable recovery
- Phone Chat, Focus, knowledge, and one reversible guarded-action workflow
- Owner acceptance
- Protected merge, installed-main rebuild, verified final backup, tag, and
  release

## Exact next action

After a cooling-off period, perform one certificate-status check. If the
certificate remains unavailable, capture a Tailscale bug report only with the
owner's approval and contact Tailscale support. Do not merge or release 0.69.0
until private HTTPS and phone acceptance pass.
