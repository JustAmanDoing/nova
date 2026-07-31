# Milestone 69 - Architecture Review

**Date:** 31 July 2026

**Review target:** Secure Tailnet Phone Access proposal

**Decision:** Approved with the controls in this review

## Architecture fit

The slice preserves NOVA's modular monolith. It adds no application service,
database, queue, cloud dependency, or second source of truth.

The runtime path is:

```text
Authenticated owner phone
        |
        | private Tailscale HTTPS
        v
Tailscale Serve on the NOVA PC
        |
        | 127.0.0.1:5173
        v
Existing frontend Nginx
        | \
        |  \ /api/
        |   v
        | Existing backend:8000
        v
Existing static NOVA interface
```

Tailscale provides the private transport. NOVA owns the same-origin application
gateway and keeps its backend private.

## Preserved boundaries

### Local-first and privacy-first

- Both published Docker ports remain bound to `127.0.0.1`.
- No router port or public listener is added.
- Tailscale Funnel is prohibited.
- No application data is uploaded by this change.

### Owner control

- Phone access requires an explicit owner command.
- Disable is available as a separate explicit command.
- The existing `X-Nova-Intent` guard remains mandatory for material actions.
- Access transport does not grant new application authority.

### Trust and origin

- The browser uses the same HTTPS origin for the interface and API.
- Nginx accepts only localhost and one configured Tailscale DNS name.
- Nginx forwards API requests with `Host: localhost`.
- The backend Host allowlist remains `localhost,127.0.0.1`.
- Backend CORS does not expand because phone requests are same-origin at
  Nginx.

### AI optionality

Focus, knowledge, intake, backup, and other deterministic core operations
remain useful when Ollama is unavailable. Phone access does not change the
existing optional chat-provider boundary.

### Modularity

The frontend API adapter continues to own browser request construction. Nginx
owns HTTP routing. The backend remains unaware of Tailscale. Windows controls
own local operational setup. These are existing module boundaries.

## Threat review

| Threat | Control |
| --- | --- |
| Public exposure | Use Serve only; reject Funnel; keep loopback binds |
| Host-header abuse | Exact frontend Host allowlist and backend localhost Host |
| Cross-origin weakening | Relative API paths; no backend CORS expansion |
| Bypassing owner approval | Existing intent header and confirmation controls |
| Accidental overwrite of another Serve service | Enable refuses a conflicting Serve configuration |
| Irreversible access change | Separate guarded disable control |
| Stale browser release | All application entry pages revalidate |
| Hidden external dependency | Desktop use remains available without Tailscale |

## Known limitation

Tailnet membership and Tailscale access-control policy remain administered by
the owner in Tailscale. This release validates the currently authenticated
owner phone and PC; it does not create a general multi-user authorization
system.

## Architecture decision

Approved. The same-origin proxy is the smallest design that makes phone access
work without weakening NOVA's backend or adding public exposure.
