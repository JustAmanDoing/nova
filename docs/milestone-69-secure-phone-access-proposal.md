# Milestone 69 Proposal - Secure Tailnet Phone Access

**Date:** 31 July 2026

**Owner decision:** Approved

**Target release:** 0.69.0

## Purpose

Make the accepted NOVA local prototype available to the owner's phone through
the owner's existing Tailscale network so daily-use validation can happen on
the device the owner intends to use.

This is a private-access prerequisite, not a public-hosting feature.

## Approved outcome

The owner can open one HTTPS address on an authenticated Tailscale device and
use the same accepted NOVA interface and API that run locally on the Windows
PC.

## Required boundaries

- Keep the frontend and backend Docker ports bound to Windows loopback.
- Use Tailscale Serve, never Tailscale Funnel.
- Do not open router ports.
- Do not add a public DNS record or public reverse proxy.
- Use one same-origin browser route for both the interface and `/api/`.
- Keep the backend Host allowlist and CORS policy local-only.
- Accept only the exact configured Tailscale DNS name at the frontend proxy.
- Preserve all owner-intent headers and approval gates.
- Do not add telemetry, cloud storage, external AI providers, plugins, agents,
  tools, email, calendar, or autonomous actions.
- Make enable, status, and disable operations explicit and reversible.

## User experience

The owner starts NOVA normally, enables phone access once, and then opens the
private Tailscale HTTPS address on the phone. NOVA continues to work locally at
`http://localhost:5173`.

If Tailscale, NOVA, or the configured private address is unavailable, the
phone-access control fails closed and explains what needs attention.

## Technical slice

1. The frontend uses relative `/api/v1/...` URLs by default.
2. The frontend Nginx container proxies `/api/` to the existing backend
   container.
3. Nginx supplies the already-allowed `localhost` Host value to the backend,
   so backend trust rules do not expand.
4. Nginx accepts only localhost and the exact configured Tailscale DNS name.
5. Tailscale Serve terminates private HTTPS and forwards to
   `127.0.0.1:5173`.
6. Windows launchers provide guarded enable, disable, and status operations.

## Excluded

- Internet access through Tailscale Funnel
- Access for unauthenticated devices
- Tailnet-wide policy redesign
- Multi-user accounts or permissions
- Public certificates outside Tailscale
- Background notification delivery
- Mobile-native applications
- Offline phone operation
- Daily-use feature expansion

## Acceptance

Milestone 69 is complete only when:

- automated backend, frontend, Windows-control, and container checks pass;
- same-origin API access works through the frontend proxy;
- unexpected Host values remain rejected;
- Docker remains loopback-only;
- Tailscale Serve is enabled without Funnel;
- the phone loads NOVA over the private HTTPS name;
- chat, Focus, knowledge, and one guarded reversible action work on the phone;
- desktop access still works;
- disable and re-enable are proven;
- a verified database backup and release evidence are recorded; and
- the owner explicitly accepts the phone workflow.

## Exact next milestone

**Milestone 70 - Phone Daily-Use Validation**

Use release 0.69.0 naturally from the phone without adding runtime authority.
Collect reliability, usability, responsiveness, battery, and approval-friction
evidence before selecting another capability.
