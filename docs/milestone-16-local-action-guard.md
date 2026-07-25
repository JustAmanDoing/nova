# Milestone 16: Local action guard

## Outcome

Nova now distinguishes read-only API requests from requests that change local
state. Every state-changing request must carry a fixed Nova intent header that
the local interface adds automatically.

## Why this is needed

Binding the API to `127.0.0.1` keeps it off the local network, and CORS prevents
an unapproved website from reading Nova's responses. CORS alone does not stop a
website from attempting a simple cross-origin form POST to some bodyless local
endpoints.

Nova now requires this header on every mutating endpoint:

```text
X-Nova-Intent: local-user-action
```

A browser cannot add that non-simple header cross-origin without first passing
a CORS preflight. Nova permits the configured local interface origin and
rejects other origins.

## Protected operations

- manual intake scan
- recommendation review
- learning reset
- approved file execution
- undo
- database backup creation
- database restore

Read-only health, inventory, search, summary, action history, recovery,
preference, backup-list, and backup-download requests remain unchanged.

## Boundary

This header is a browser request-integrity guard, not user authentication. Nova
remains a single-user local application with no remote access by default. The
local interface sends the header automatically, so normal use requires no new
prompt or setup.
