# Milestone 28: Fresh dashboard entry page

## Outcome

Nova's production web server now requires the browser to revalidate
`index.html` instead of silently reusing a stale copy after an update.

## Why it matters

The dashboard build gives JavaScript and CSS assets content-based filenames. A
cached older entry page can refer to assets that no longer exist after the
container is rebuilt. Revalidating the small entry page keeps those references
in sync while hashed assets retain normal browser behavior.

Nginx applies `expires -1` only to `index.html`, producing
`Cache-Control: no-cache`. This permits efficient validation without storing
Nova API data, which remains separately protected by `no-store`.

## Verification

A structural backend test protects the Nginx rule, and the production runtime
smoke test verifies the cache header from the live dashboard container.
