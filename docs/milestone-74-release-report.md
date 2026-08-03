# Milestone 74 - Final Release Report

**Date:** 3 August 2026

**Release:** 0.74.0

**Status:** Release approved; evidence-only integration, tag, and GitHub
publication remain

## Finding and correction

Daily use showed that NOVA answered a request for fuller assistance with
generic boilerplate and a misleading blanket statement about documents and
tools. The implemented correction gives the local model a verified inventory
of NOVA's current capabilities and exact limits, plus rules that prevent
examples from promising unavailable operations.

No runtime authority was expanded. The change affects Chat guidance and its
regression tests only; all existing approval, privacy, selected-document,
network, storage, and action boundaries remain intact.

## Repository integration

- Product PR: [#20](https://github.com/JustAmanDoing/nova/pull/20)
- Integration method: merge commit
- Accepted feature head: `9963bc2d1c07dec41ca672bb661cea6661676821`
- Product merge commit: `4057e071392ad1b2c5686093112040eb0645ebbe`
- Feature branch preserved: `agent/milestone-74-capability-guidance`
- Protected checks passed:
  - Backend quality
  - Frontend quality
  - Windows controls
  - Production runtime
- GitHub Actions run:
  [30797894703](https://github.com/JustAmanDoing/nova/actions/runs/30797894703)

## Exact merged-main verification

The Windows checkout, `origin/main`, and product merge commit all resolved to
`4057e071392ad1b2c5686093112040eb0645ebbe`. The merged tree matched the
accepted feature head exactly.

NOVA was rebuilt and restarted from that exact merged `main` source. Checks
passed:

- backend and frontend containers running;
- backend healthy;
- local health version `0.74.0`;
- private same-origin health version `0.74.0`;
- local and private Chat pages returned HTTP 200;
- active database read-only integrity returned `ok`;
- Docker remained loopback-only;
- Tailscale Serve remained tailnet-only;
- corrected log scan found zero error-severity and zero HTTP 5xx matches; and
- the exact-main `qwen3:8b` response accurately described current capabilities
  and limits without promising unavailable actions.

The exact-main synthetic verification conversation
`71a0e75d-6b0a-4cf7-ac50-5b474f0f8e40` was archived after testing rather than
deleted.

## Recovery evidence

Exact-main verification created backup
`nova-20260803T083807.758465Z.db`. NOVA verified it and the independently
recalculated host SHA-256 matched:

`200faef35f783653cb368205c3a3c475597b5f0d5a251f326c64b9640323d850`

## Acceptance summary

- Backend: Ruff and strict mypy passed; 149 tests passed with 93.30 percent
  coverage.
- Frontend: ESLint and TypeScript passed; 48 tests and production build passed.
- Windows controls and Compose configuration passed.
- Installed candidate and exact merged-main runtime checks passed.
- Real local-model checks passed.
- Physical-owner acceptance passed.
- No secret, generated source artifact, debug marker, dependency, schema,
  endpoint, provider, listener, or permission expansion was introduced.

The existing non-failing React `act(...)` warnings remain a low-priority test
harness cleanup item and are not caused by this backend guidance correction.

## Completion and next milestone

- Practical local NOVA prototype: 100 percent.
- Broader long-term NOVA vision: approximately 86 percent.
- Milestone 74 implementation and acceptance: 100 percent.

After this evidence-only change passes protected integration, tag the resulting
`main` commit as `v0.74.0`, publish GitHub Release 0.74.0, verify local and remote
tag alignment, and begin **Milestone 75 - Evidence-Led Next Capability
Selection** as proposal and review work only.
