# Milestone 69 - Secure Tailnet Phone Access Implementation

**Date:** 31 July 2026

**Target release:** 0.69.0

**Status:** Implemented on feature branch; runtime and owner acceptance pending

## Implemented

- The production browser API default is now relative and same-origin.
- Frontend Nginx proxies `/api/` to the existing backend container.
- Streaming is unbuffered and upstream timeouts remain bounded.
- The backend receives `Host: localhost`; its Host allowlist and CORS policy
  remain unchanged.
- The frontend default private Host is `nova.invalid`.
- The exact Tailscale DNS name is read from the authenticated local Tailscale
  state, validated as a `.ts.net` name, and written only to ignored local
  configuration.
- All application entry pages revalidate after updates.
- Content Security Policy `connect-src` is reduced to `'self'`.
- Windows controls now provide guarded phone enable, disable, and status.
- Enable refuses public Funnel and any unowned Serve configuration.
- Enable now stops before rebuilding when tailnet HTTPS consent is missing,
  reports the exact owner-approval URL, and explains the Windows administrator
  requirement instead of waiting silently in the Tailscale command.
- Funnel detection inspects Tailscale's `AllowFunnel` flags rather than treating
  the shared Serve/Funnel status document as public merely because it is
  non-empty. Private Serve configurations with false flags remain allowed;
  any true flag still triggers the fail-closed reset.
- Disable refuses to remove Serve when its live configuration differs from
  the exact configuration NOVA recorded.
- Backend and frontend versions are aligned at `0.69.0`.

## Source changes

- `frontend/src/lib/api.ts`
- `frontend/default.conf.template`
- `frontend/Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `scripts/Nova.ps1`
- `scripts/Test-NovaScripts.ps1`
- `Phone Access On.cmd`
- `Phone Access Off.cmd`
- `Check Phone Access.cmd`
- version, CI, contract-test, README, architecture, and roadmap records

## Safety behavior

Phone access changes transport only. It does not change the database, knowledge
model, action model, approval boundary, file workflow, provider adapter, or
application authority. All material API calls still require the existing local
owner-intent header and any domain-specific confirmation.

The Windows control stores the exact Serve configuration it created under
ignored local runtime data. It will not reset Serve unless the current
configuration still matches that record.

## Evidence collected so far

- Frontend lint: passed
- Frontend type checking: passed
- Frontend tests: 46 passed
- Frontend production build: passed
- Backend Ruff: passed
- Backend mypy: passed
- Backend tests: 144 passed
- Backend coverage: 93.43%
- Windows structural controls: passed
- Docker Compose validation: passed
- Production backend and frontend builds: passed
- Installed direct backend health: passed at 0.69.0
- Installed same-origin health: passed at 0.69.0
- Exact configured private Host through Nginx: passed
- Unexpected frontend Host: dropped
- Unexpected backend Host: rejected
- Windows Docker listeners: loopback-only
- Tailscale Funnel: empty

## Pending acceptance

- One-time owner authorization of Tailscale Serve HTTPS - complete
- Exact private Serve configuration with Funnel disabled - complete
- Private HTTPS health through Tailscale - blocked by a Tailscale ACME DNS
  record HTTP 500; see `docs/milestone-69-acceptance.md`
- Disable and re-enable recovery
- Phone chat, Focus, knowledge, and guarded action workflow
- Owner acceptance
- Protected pull request, merged-main verification, installed-main rebuild,
  final backup, tag, and release

## Exact next milestone

After release acceptance, proceed to **Milestone 70 - Phone Daily-Use
Validation** without adding runtime authority.
