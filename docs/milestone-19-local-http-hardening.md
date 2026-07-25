# Milestone 19: Local HTTP hardening

## Outcome

Nova now rejects unexpected Host headers at both local HTTP services and serves
the dashboard with restrictive browser security headers.

## Host boundary

The backend accepts only the configured local hosts. The default Docker
deployment allows:

```text
localhost
127.0.0.1
```

The frontend Nginx service serves the dashboard only for those same hosts. Its
default virtual host closes requests for any other Host value. This reduces the
local DNS-rebinding surface while preserving normal use through
`http://localhost:5173`.

Backend hosts remain configurable with `NOVA_ALLOWED_HOSTS` as a comma-separated
list. Adding network names does not publish the ports; Docker remains bound to
`127.0.0.1` by default.

## Browser protections

The dashboard now sends:

- a Content Security Policy limited to Nova's static assets and two local API
  origins
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- same-origin opener and resource policies
- `Referrer-Policy: no-referrer`
- a Permissions Policy disabling camera, microphone, and geolocation

HTTPS-only controls are deliberately omitted because the approved deployment is
local HTTP on loopback.

## Verification

Backend tests cover accepted and rejected Host values. The production runtime
smoke test verifies the security headers and confirms that both Nginx and
FastAPI reject an unexpected host after the real containers start.
