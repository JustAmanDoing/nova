# Milestone 69 - Engineering Review

**Date:** 31 July 2026

**Review target:** Secure Tailnet Phone Access proposal and architecture

**Decision:** Approved for bounded implementation

## Implementation requirements

1. Change the production browser API default from an absolute localhost URL to
   a relative same-origin URL.
2. Add an Nginx `/api/` reverse proxy to the existing backend service.
3. Keep chat streaming unbuffered and use bounded upstream timeouts.
4. Parameterize one exact Tailscale DNS name without committing the owner's
   tailnet name to source.
5. Keep the default configured phone Host deliberately invalid so a fresh
   checkout remains localhost-only.
6. Keep both Docker port publications on `127.0.0.1`.
7. Add explicit Windows controls for enable, disable, and status.
8. Refuse to replace an unrelated Tailscale Serve configuration.
9. Do not enable or modify Funnel.
10. Bump backend and frontend versions together to `0.69.0`.

## Required verification

- Backend lint, type checking, and tests
- Frontend lint, type checking, tests, and production build
- Windows controller parsing and structural tests
- Docker Compose validation and clean production build
- Direct backend health
- Same-origin health through the frontend
- Chat streaming through the frontend proxy
- Guarded mutation through the frontend proxy
- Localhost dashboard access
- Exact configured private Host access
- Rejection of unexpected frontend and backend Host values
- Security headers and entry-page cache controls
- Loopback-only Windows listeners
- Tailscale Serve enabled and Funnel empty
- Disable and re-enable recovery
- Phone browser acceptance
- Verified backup and database integrity

## Stop conditions

Stop release work if any check shows:

- a non-loopback Docker listener;
- a Tailscale Funnel configuration;
- backend CORS or Host expansion to the tailnet;
- acceptance of arbitrary Host values;
- material actions succeeding without the owner-intent guard;
- replacement of an unrelated Serve configuration;
- different installed and source versions;
- a failing database integrity check; or
- a phone route that bypasses the same-origin gateway.

## Engineering decision

Approved. The bounded implementation reuses Tailscale's private transport and
Nginx's existing gateway role instead of introducing a new remote-access
service. Runtime acceptance remains required before release.
