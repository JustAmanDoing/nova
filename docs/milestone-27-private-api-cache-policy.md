# Milestone 27: Private API cache policy

## Outcome

Every response under Nova's versioned API path now tells browsers and
intermediaries not to store it.

## Policy

API responses include:

```text
Cache-Control: no-store
Pragma: no-cache
```

This covers health data, filenames, extracted text, evidence, review records,
action history, learning preferences, and database backup responses. Static
dashboard assets keep their ordinary delivery behavior.

The policy complements Nova's loopback-only network binding, Host validation,
CORS boundary, local-action guard, and restrictive dashboard headers. It does
not replace filesystem permissions or operating-system security.

## Verification

The backend health test asserts both headers. The production runtime smoke test
also checks `Cache-Control: no-store` from the live container.
