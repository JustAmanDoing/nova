# Milestone 23: Current ASGI test transport

## Purpose

Starlette 1.2 introduced `httpx2` support and Starlette 1.3 now recommends it
for `TestClient`. Continuing to install the deprecated `httpx` transport leaves
Nova's test suite on a compatibility path that Starlette plans to remove.

## Change

Nova's development dependencies now install `httpx2` 2.x. Application code and
production containers are unchanged; this package is used only by backend
tests.

The migration follows Starlette's official TestClient guidance:

- <https://www.starlette.io/testclient/>
- <https://www.starlette.io/release-notes/>

The full backend suite remains the compatibility contract for request behavior,
lifespan handling, headers, downloads, and local action guards.
